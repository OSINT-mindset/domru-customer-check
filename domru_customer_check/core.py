import asyncio
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


class Processor:
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
        self.domains = [d.get('domain') for d in json]
        return self.domains

    async def close(self):
        await self.session.close()

    async def request(self, input_data: InputData) -> OutputDataList:
        status = 0
        result = None
        error = None
        output_data = []

        HEADERS = {
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

        try:
            url = 'https://api-profile.dom.ru/v1/unauth/contract-asterisked?contact={}&isActive=1'
            url = url.format(input_data.value)

            HEADERS.update({
                'domain': input_data.domain,
                'origin': f'https://{input_data.domain}.dom.ru',
                'referer': f'https://{input_data.domain}.dom.ru/',
            })

            response = await self.session.get(url, headers=HEADERS)
            result = await response.json()
            for c in result.get('contacts', []):
                contact_id = c.get('contactId')
                agreement_id = c.get('agreementId')
                contact_type = c.get('contactType')
                row = c.get('row')
                address = c.get('address')

                output_data.append(OutputData(
                    status,
                    error,
                    contact_id=contact_id,
                    contact_type=contact_type,
                    agreement_id=agreement_id,
                    row=row,
                    address=address,
                ))

        except Exception as e:
            print(e)
            error = e

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
