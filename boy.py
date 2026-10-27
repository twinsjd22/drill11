from pico2d import load_image, get_time, get_canvas_width, clamp, SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT
from transitions import Machine


class Boy:
    # 상태 머신: IDLE, SLEEP, RUN 세 상태
    states = ['IDLE', 'SLEEP', 'RUN']

    # 상태 전이 규칙
    transitions = [
        {'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},  # IDLE로 5초가 지나면 SLEEP
        {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},  # SLEEP에서 SPACE를 누르면 IDLE
        {'trigger': 'arrow_down', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},  # IDLE 또는 SLEEP에서 방향키를 누르면 RUN
        {'trigger': 'arrow_up', 'source': 'RUN', 'dest': 'IDLE'},  # RUN에서 방향키를 떼면 IDLE
    ]

    RUN_SPEED = 5  # 한 프레임에 이동하는 픽셀 수

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1  # 바라보는 방향: 1 오른쪽, -1 왼쪽
        self.dir = 0  # 이동 방향: 1 오른쪽, -1 왼쪽, 0 정지
        self.image = load_image('animation_sheet.png')

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

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_SPACE:
                self.space_down()
            elif event.key == SDLK_RIGHT:
                self.arrow_down(1)
            elif event.key == SDLK_LEFT:
                self.arrow_down(-1)
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

    def draw(self):
        if self.state == 'IDLE':
            self.idle_draw()
        elif self.state == 'SLEEP':
            self.sleep_draw()
        elif self.state == 'RUN':
            self.run_draw()
