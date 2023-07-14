import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import Body, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from random import choice, randint
from time import time


app = FastAPI(
    docs_url=None,
    redoc_url=None,
)
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
            if interval == 0:
                raise ValueError('Interval cannot be 0')
            driftoffset = int(time()) % interval
            if run_first:
                asyncio.create_task(func(*args, **kwargs))
            if interval == 1:
                while True:
                    await asyncio.sleep(interval)
                    asyncio.create_task(func(*args, **kwargs))
            else:
                while True:
                    offset = int(time()) % interval
                    if (driftoffset+1) % interval == offset:
                        logging.debug(
                            f'Adjusting {func.__name__} for time drift'
                        )
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
            logging.debug(f'Adding service: {service}')
            self._pending_services.append(service)

    async def _remove_random_service(self):
        if len(self._active_services) > 1:
            service = choice(self._active_services)
            logging.debug(f'Removing service: {service}')
            self._active_services.remove(service)

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

    async def simulate_scoreboard(self, delay=None):
        if delay:
            await asyncio.sleep(delay)
        logging.info(f'Starting simulation')
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


def check_authorization(request):
    token = request.cookies.get('supersecuretoken')
    if token == 'c3VwZXJzZWN1cmVhdXRob3JpemF0aW9udG9rZW4=':
        return True
    else:
        return False


@app.on_event('startup')
async def start_simulation():
    logging.basicConfig(
        datefmt='%Y-%m-%d %X',
        format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                f"app_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.log",
                mode='w'),
        ],
        level=logging.DEBUG,
    )

    # UTC time to start simulation
    now = datetime.utcnow()
    if now.minute or now.second:
        start_time = now.replace(minute=0, second=0, microsecond=0) \
                     + timedelta(hours=1)
        delay = (start_time - now).seconds
        startftime = start_time.strftime('%Y-%m-%d %X UTC+00:00')
        delayftime = f'{delay//60:02d}:{delay%60:02d}'
        logging.info(f"Starting simulation in {delayftime} at {startftime}")
    else:
        delay = None
    asyncio.create_task(scoreboard.simulate_scoreboard(delay=delay))


@app.on_event('shutdown')
async def end_simulation():
    scoreboard.stop_tasks()
    logging.shutdown()


@app.get('/login')
@app.get('/login.html')
async def login(request: Request):
    ctx = {
        'request': request,
    }
    return templates.TemplateResponse('login.html', ctx)


@app.post('/login')
@app.post('/login.html')
async def check_login(request: Request, response: Response):
    body = await request.body()
    form = dict(params.split(b'=') for params in body.split(b'&'))
    if form[b'action'] == b'login' \
            and form[b'name'] == b'user' \
            and form[b'password'] == b'password':
        response.set_cookie(
            key='supersecuretoken',
            value='c3VwZXJzZWN1cmVhdXRob3JpemF0aW9udG9rZW4='
        )
        response.status_code=302
        response.headers['location'] = 'scoreboard'
        return response
    else:
        ctx = {
            'request': request,
        }
        return templates.TemplateResponse('login.html', ctx)


@app.get('/availability')
@app.get('/availability.html')
async def availability(request: Request, response: Response):
    if check_authorization(request):
        ctx = {
            'request': request,
            'availabilities': scoreboard.availabilities,
        }
        return templates.TemplateResponse('availability.html', ctx)
    else:
        response.status_code=302
        response.headers['location'] = 'login'
        return response


@app.get('/')
@app.get('/scoreboard')
@app.get('/scoreboard.html')
async def scoreboard(request: Request, response: Response):
    if check_authorization(request):
        ctx = {
            'request': request,
            'scores': scoreboard.scores,
        }
        return templates.TemplateResponse('scoreboard.html', ctx)
    else:
        response.status_code=302
        response.headers['location'] = 'login'
        return response


@app.get('/logout')
@app.get('/logout.html')
async def logout(response: Response):
    response.status_code=302
    response.headers['location'] = 'login'
    response.delete_cookie(key='supersecuretoken')
    return response


scoreboard = Scoreboard()

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=80)