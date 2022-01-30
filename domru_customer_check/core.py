import asyncio
from json import JSONEncoder
from typing import List, Any

from aiohttp import TCPConnector, ClientSession

from .executor import AsyncioProgressbarQueueExecutor, AsyncioSimpleExecutor


class InputData:
    def __init__(self, value: str, domain: str):
        self.value = value
        self.domain = domain

    def __str__(self):
        return f'{self.value} ({self.domain})'

    def __repr__(self):
        return f'{self.value} ({self.domain})'


class OutputData:
    def __init__(self, code, error, *args, **kwargs):
        self.code = code
        self.error = error
        for k, v in kwargs.items():
            self.__dict__[k] = v

    @property
    def fields(self):
        fields = list(self.__dict__.keys())
        fields.remove('error')
        fields.remove('code')

        return fields

    def __str__(self):
        error = ''
        if self.error:
            error = f' (error: {str(self.error)}'

        result = ''

        for field in self.fields:
            field_pretty_name = field.title().replace('_', ' ')
            value = self.__dict__.get(field)
            if value:
                result += f'{field_pretty_name}: {str(value)}\n'

        result += f'{error}'
        return result


class OutputDataList:
    def __init__(self, input_data: InputData, results: List[OutputData]):
        self.input_data = input_data
        self.results = results

    def __repr__(self):
        return f'Target {self.input_data}:\n' + '--------\n'.join(map(str, self.results))


class OutputDataListEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, OutputDataList):
            return {'input': o.input_data, 'output': o.results}
        elif isinstance(o, OutputData):
            return {k:o.__dict__[k] for k in o.fields}
        else:
            return o.__dict__


class Processor:
    REDUNDANT_DOMAINS = set({
        'sbor',    # Сосновый бор == Санкт-Петербург (interzet)
        'vlz',     # Волжский == Волгоград (volgograd)
        # Пермь (perm)
        'ber',     # Березники
        'kungur',  # Кунгур
        'chus',    # Чусовой
        'slk',     # Соликамск
    })

    CONTACTS = {
        '2': 'Phone/Agreement',
        '1': 'Email',
        '3': 'Address',
    }

    def get_contact_type(self, contact):
        return self.CONTACTS.get(str(contact), 'unknown')

    def __init__(self, *args, **kwargs):
        from aiohttp_socks import ProxyConnector

        # make http client session
        proxy = kwargs.get('proxy')
        self.proxy = proxy
        if proxy:
            connector = ProxyConnector.from_url(proxy, ssl=False)
        else:
            connector = TCPConnector(ssl=False)

        self.session = ClientSession(
            connector=connector, trust_env=True
        )
        if kwargs.get('no_progressbar'):
            self.executor = AsyncioSimpleExecutor()
        else:
            self.executor = AsyncioProgressbarQueueExecutor()

        # domru setup
        self.domains = []

    async def get_domains(self):
        HEADERS = {
            'Host': 'api-mobile.domru.ru',
            'User-Agent': 'com.ertelecom.agent/3.31.3 (Android 28)',
            'app-version': '3.31.3',
        }

        req = await self.session.get('https://api-mobile.domru.ru/v1/geography/all-cities?active=1', headers=HEADERS)
        json = await req.json()
        domains = [d.get('domain') for d in json]

        pure_domains = list(set(domains) - set(self.REDUNDANT_DOMAINS))
        self.domains = pure_domains

        return self.domains

    async def close(self):
        await self.session.close()

    async def request(self, input_data: InputData) -> OutputDataList:
        HEADERS_PROFILE = {
            'authority': 'api-profile.dom.ru',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
            'accept': 'application/json, text/plain, */*',
            'authorization': 'Bearer unauth',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'en,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7',
        }

        HEADERS_MOBILE = {
            'Host': 'api-mobile.domru.ru',
            'accept-encoding': 'gzip',
            'user-agent': 'com.ertelecom.agent/3.31.3 (Android 28)',
            'app-version': '3.31.3',
            'accept': '*/*',
        }

        def is_phone(value):
            return len(value) == 11 and (value.startswith('89') or value.startswith('79'))

        async def get_api_mobile(contact):
            output_data = []

            try:
                url = f'https://api-mobile.domru.ru/v1/agreement/list-contact'

                HEADERS_MOBILE.update({
                    'domain': input_data.domain,
                })

                response = await self.session.post(url, headers=HEADERS_MOBILE, data={'username': contact})
                result = await response.json()
                # print(result)

                for a in result.get('agreements'):
                    output_data.append(OutputData(
                        status,
                        error,
                        value=a['value'],
                        contact_type=self.get_contact_type(a['sendType']),
                        contact_id=a['contactId'],
                        agreement_id=a['agreementId'],
                        domain=input_data.domain,
                    ))

            except Exception as e:
                print(e)

            return output_data

        async def get_api_profile(contact):
            output_data = []
            contacts = []

            try:
                url = f'https://api-profile.dom.ru/v1/unauth/contract-asterisked?contact={contact}&isActive=1'

                HEADERS_PROFILE.update({
                    'domain': input_data.domain,
                    'origin': f'https://{input_data.domain}.dom.ru',
                    'referer': f'https://{input_data.domain}.dom.ru/',
                })

                response = await self.session.get(url, headers=HEADERS_PROFILE)
                result = await response.json()
                # print(result)

                for c in result.get('contacts', []):
                    contact_id = c.get('contactId')
                    agreement_id = c.get('agreementId')
                    contact_type = self.get_contact_type(c.get('contactType'))
                    value = c.get('row')
                    address = c.get('address')

                    output_data.append(OutputData(
                        status,
                        error,
                        value=value,
                        contact_type=contact_type,
                        contact_id=contact_id,
                        agreement_id=agreement_id,
                        domain=input_data.domain,
                        address=address,
                    ))

                    # encoded (encrypted?) agreement ID
                    # base64(smth(id))
                    row_enc = c.get('rowEnc')
                    if row_enc:
                        contacts.append(row_enc)

                # additional request to mobile api to get full agreement ID
                if output_data and is_phone(contact):
                    c = await get_api_mobile(contact)
                    output_data += c

            except Exception as e:
                print(e)

            return output_data, contacts

        status = 0
        result = None
        error = None
        output_data = []

        contacts = [input_data.value]
        while contacts:
            contact = contacts.pop()
            o, c = await get_api_profile(contact)
            contacts += c
            output_data += o

        results = None

        if output_data:
            results = OutputDataList(input_data, output_data)

        return results


    async def process(self, input_data: List[InputData]) -> List[OutputDataList]:
        tasks = [
            (
                self.request, # func
                [i],          # args
                {}            # kwargs
            )
            for i in input_data
        ]

        results = await self.executor.run(tasks)

        return results
