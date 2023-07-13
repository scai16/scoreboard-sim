import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from random import choice, randint
from time import gmtime, strftime, time


app = FastAPI(docs_url=None, redoc_url=None)
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


def delay(seconds=0, minutes=0, hours=0):
    def delay_task(func):
        async def wrapper(*args, **kwargs):
            await asyncio.sleep(seconds + minutes*60 + hours*60*60)
            asyncio.create_task(func(*args, **kwargs))
        return wrapper
    return delay_task


def repeat_every(seconds=0, minutes=0, hours=0, run_first=True):
    def repeat_task(func):
        async def wrapper(*args, **kwargs):
            interval = seconds + minutes*60 + hours*60*60
            driftoffset = int(time()) % interval
            if run_first:
                asyncio.create_task(func(*args, **kwargs))
            while True:
                offset = int(time()) % interval
                if (driftoffset+1) % interval == offset:
                    logging.debug(f'Adjusting {func.__name__} for time drift')
                    await asyncio.sleep(interval-1)
                else:
                    await asyncio.sleep(interval)
                asyncio.create_task(func(*args, **kwargs))
        return wrapper
    return repeat_task


class Scoreboard:
    def __init__(self):
        self._all_services = [
            'containerchall2',
            'corewar-n2',
            'mambo',
            'nivisor',
            'perplexity',
            'router-pi',
            'web4factory',
        ]
        self._pending_services = ['web4factory', 'router-pi']
        self._active_services = []
        self._tasks = []
        self.availabilities = {}
        self.scores = {
            './V /home/r/.bin/tw': 0,
            'Balsn.217@TSJ.tw': 0,
            'CP-r3kapig': 0,
            'DiceGuesser': 0,
            'Katzebin': 0,
            'Maple Mallard Magistrates': 0,
            'OSUSEC': 0,
            'PTB_WTL': 0,
            'Sauercloud': 0,
            'Shellphish': 0,
            'StarBugs': 0,
            'Straw Hat': 0,
            'Water Paddler': 0,
            'perfect r✪✪✪t': 0,
            'the new organizers': 0,
            '侍': 0,
        }

    async def _add_random_service(self):
        inactive_services = set(self._all_services)-set(self._active_services)
        if inactive_services:
            service = choice(list(inactive_services))
            self._pending_services.append(service)

    async def _remove_random_service(self):
        if len(self._active_services) > 1:
            self._active_services.remove(choice(self._active_services))

    @repeat_every(minutes=10)
    async def _generate_round(self):
        logging.info('Updating availabilities')
        round_sla = {}
        for service in self._active_services:
            if randint(1, 100) >= 10:
                round_sla[service] = 'true'
            else:
                round_sla[service] = 'false'
        while self._pending_services:
            new_service = self._pending_services.pop()
            round_sla[new_service] = 'true'
            self._active_services.append(new_service)
        self.availabilities[len(self.availabilities)+1] = round_sla
    
    @repeat_every(minutes=5, run_first=False)
    async def _update_scores(self):
        logging.info('Updating scoreboard')
        for team in self.scores:
            if team in ('侍', 'Shellphish'):
                multiplier = randint(0, 10)
                if multiplier == 0:
                    pass
                elif multiplier == 10:
                    self.scores[team] += randint(0, 110) * 2
                else:
                    self.scores[team] += randint(0, 110)
            else:
                multiplier = randint(0, 10)
                if multiplier == 0:
                    pass
                elif multiplier == 10:
                    self.scores[team] += randint(0, 100) * 2
                else:
                    self.scores[team] += randint(0, 100)

    @delay(hours=4)
    @repeat_every(hours=1)
    async def _change_random_services(self):
        logging.info('Updating services')
        change = randint(0, 100-len(self._active_services))
        if change < 10 or change > 89:
            if len(self._active_services) <= 1:
                await self._add_random_service()
            elif len(self._active_services) == len(self._all_services):
                await self._remove_random_service()
            else:
                if change < 10:
                    await self._remove_random_service()
                elif change > 89:
                    await self._add_random_service()

    def simulate_scoreboard(self):
        tasks = [
            self._generate_round,
            self._update_scores,
            self._change_random_services,
        ]
        for task in tasks:
            self._tasks.append(asyncio.create_task(task()))

    def stop_tasks(self):
        for task in self._tasks:
            task.cancel()


@app.on_event('startup')
async def start_simulation():
    scoreboard.simulate_scoreboard()


@app.get('/login', response_class=HTMLResponse)
@app.get('/login.html', response_class=HTMLResponse)
async def scoreboard(request: Request):
    ctx = {
        'request': request,
    }
    return templates.TemplateResponse('login.html', ctx)


@app.get('/availability', response_class=HTMLResponse)
@app.get('/availability.html', response_class=HTMLResponse)
async def availability(request: Request):
    ctx = {
        'request': request,
        'availabilities': scoreboard.availabilities,
    }
    return templates.TemplateResponse('availability.html', ctx)


@app.get('/scoreboard', response_class=HTMLResponse)
@app.get('/scoreboard.html', response_class=HTMLResponse)
async def scoreboard(request: Request):
    ctx = {
        'request': request,
        'scores': scoreboard.scores,
    }
    return templates.TemplateResponse('scoreboard.html', ctx)


@app.on_event('shutdown')
async def end_simulation():
    scoreboard.stop_tasks()
    logging.shutdown()


print('Waiting until the next minute to start.')
while gmtime().tm_sec:
    pass

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S',
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"app_{strftime('%Y%m%d%H%M%S')}.log", mode='w'),
    ],
    level=logging.DEBUG,
)

scoreboard = Scoreboard()