from pico2d import load_image, get_time, get_canvas_width, clamp, SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a
from transitions import Machine


class AutoRun:
    # 자동 무적 런 상태: 키 조작 없이 스스로 좌우로 달리기
    SPEED = 10  # 한 프레임에 이동하는 픽셀 수 (RUN의 2배)
    SCALE = 2  # 확대 배율
    DURATION = 5  # 지속 시간(초)

    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        self.start_time = get_time()  # 5초 타이머 시작
        self.boy.dir = self.boy.face_dir  # 바라보던 방향으로 출발

    def exit(self):
        self.boy.dir = 0

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8
        boy.x += boy.dir * AutoRun.SPEED

        # 좌우 끝에 닿으면 자동으로 방향 전환 (커진 만큼 여백도 늘림)
        margin = 25 * AutoRun.SCALE
        if boy.x > get_canvas_width() - margin:
            boy.x = get_canvas_width() - margin
            boy.dir = boy.face_dir = -1
        elif boy.x < margin:
            boy.x = margin
            boy.dir = boy.face_dir = 1

        if get_time() - self.start_time > AutoRun.DURATION:
            boy.time_out()  # 5초가 지나면 IDLE로 복귀

    def draw(self):
        boy = self.boy
        size = 100 * AutoRun.SCALE
        y = boy.y + (AutoRun.SCALE - 1) * 50  # 커져도 발이 땅에 닿도록 위로 올림
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 100, 100, 100, boy.x, y, size, size)
        else:
            boy.image.clip_draw(boy.frame * 100, 0, 100, 100, boy.x, y, size, size)


class Boy:
    # 상태 머신: IDLE, SLEEP, RUN, AUTO_RUN 네 상태
    states = ['IDLE', 'SLEEP', 'RUN', 'AUTO_RUN']

    # 상태 전이 규칙
    transitions = [
        {'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},  # IDLE로 5초가 지나면 SLEEP
        {'trigger': 'time_out', 'source': 'AUTO_RUN', 'dest': 'IDLE'},  # AUTO_RUN으로 5초가 지나면 IDLE
        {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},  # SLEEP에서 SPACE를 누르면 IDLE
        {'trigger': 'arrow_down', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},  # IDLE 또는 SLEEP에서 방향키를 누르면 RUN
        {'trigger': 'arrow_up', 'source': 'RUN', 'dest': 'IDLE'},  # RUN에서 방향키를 떼면 IDLE
        {'trigger': 'a_down', 'source': 'IDLE', 'dest': 'AUTO_RUN'},  # IDLE에서 a를 누르면 AUTO_RUN
    ]

    RUN_SPEED = 5  # 한 프레임에 이동하는 픽셀 수

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1  # 바라보는 방향: 1 오른쪽, -1 왼쪽
        self.dir = 0  # 이동 방향: 1 오른쪽, -1 왼쪽, 0 정지
        self.image = load_image('animation_sheet.png')
        self.auto_run = AutoRun(self)  # AUTO_RUN 상태 처리를 맡을 상태 객체

        # 현재 상태에 없는 트리거(예: IDLE에서 SPACE)는 무시
        self.machine = Machine(model=self, states=Boy.states, transitions=Boy.transitions,
                               initial='IDLE', ignore_invalid_triggers=True)
        self.idle_start_time = get_time()  # 처음 IDLE 상태는 on_enter가 호출되지 않으므로 직접 타이머 시작

    # IDLE 상태: IDLE 애니메이션 반복 재생
    def on_enter_IDLE(self):
        self.idle_start_time = get_time()  # IDLE로 돌아올 때마다 5초 타이머 다시 시작

    def idle_do(self):
        self.frame = (self.frame + 1) % 8
        if get_time() - self.idle_start_time > 5:
            self.time_out()

    def idle_draw(self):
        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)

    # SLEEP 상태: IDLE 애니메이션을 90도 눕혀서 재생
    def sleep_do(self):
        self.frame = (self.frame + 1) % 8

    def sleep_draw(self):
        if self.face_dir == 1:
            self.image.clip_composite_draw(self.frame * 100, 300, 100, 100,
                                           3.141592 / 2, '', self.x - 25, self.y - 25, 100, 100)
        else:
            self.image.clip_composite_draw(self.frame * 100, 200, 100, 100,
                                           -3.141592 / 2, '', self.x + 25, self.y - 25, 100, 100)

    # RUN 상태: 왼쪽/오른쪽을 dir 값 하나로 구분해서 달리기
    def on_enter_RUN(self, dir):
        self.dir = self.face_dir = dir

    def on_exit_RUN(self):
        self.dir = 0

    def run_do(self):
        self.frame = (self.frame + 1) % 8
        self.x += self.dir * Boy.RUN_SPEED
        self.x = clamp(25, self.x, get_canvas_width() - 25)  # 화면 밖으로 나가지 않게

    def run_draw(self):
        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 100, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 0, 100, 100, self.x, self.y)

    # AUTO_RUN 상태: AutoRun 상태 클래스에 처리를 맡김
    def on_enter_AUTO_RUN(self):
        self.auto_run.enter()

    def on_exit_AUTO_RUN(self):
        self.auto_run.exit()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_SPACE:
                self.space_down()
            elif event.key == SDLK_RIGHT:
                self.arrow_down(1)
            elif event.key == SDLK_LEFT:
                self.arrow_down(-1)
            elif event.key == SDLK_a:
                self.a_down()
        elif event.type == SDL_KEYUP:
            if event.key in (SDLK_LEFT, SDLK_RIGHT):
                self.arrow_up()

    def update(self):
        if self.state == 'IDLE':
            self.idle_do()
        elif self.state == 'SLEEP':
            self.sleep_do()
        elif self.state == 'RUN':
            self.run_do()
        elif self.state == 'AUTO_RUN':
            self.auto_run.do()

    def draw(self):
        if self.state == 'IDLE':
            self.idle_draw()
        elif self.state == 'SLEEP':
            self.sleep_draw()
        elif self.state == 'RUN':
            self.run_draw()
        elif self.state == 'AUTO_RUN':
            self.auto_run.draw()
