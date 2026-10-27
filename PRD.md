# PRD: 소년 자동 무적 런(AutoRun) 상태 추가

## 1. 개요

현재 `main.py`로 실행되는 게임에서 소년(`Boy`)은 `IDLE`, `SLEEP`, `RUN` 세 가지 상태를 가진다.
이번 작업에서는 **자동 무적 런(AUTO_RUN)** 상태를 새로 추가하여, 키를 계속 누르지 않아도 소년이
화면 좌우를 빠르고 크게 달리다가 5초가 지나면 IDLE로 돌아오도록 만든다.

- 대상 파일: `boy.py` (상태 머신, `AutoRun` 상태 클래스), 필요 시 `main.py`
- 사용 라이브러리: `pico2d`, `transitions` (기존과 동일)

## 2. 현재 구조

`Boy` 클래스는 `transitions.Machine`으로 상태를 관리하고, 상태마다 `xxx_do()`(갱신)와 `xxx_draw()`(그리기)
메서드를 두어 `update()` / `draw()`에서 현재 상태에 맞는 메서드를 호출한다.

| 트리거 | 출발 상태 | 도착 상태 | 설명 |
|---|---|---|---|
| `time_out` | IDLE | SLEEP | IDLE로 5초 경과 |
| `space_down` | SLEEP | IDLE | SPACE 키 누름 |
| `arrow_down(dir)` | IDLE, SLEEP | RUN | 방향키 누름 |
| `arrow_up` | RUN | IDLE | 방향키 뗌 |

`ignore_invalid_triggers=True`이므로 현재 상태에 정의되지 않은 트리거는 무시된다.

## 3. 요구사항

### 3.1 기능 요구사항

| ID | 요구사항 |
|---|---|
| FR-1 | **IDLE 상태**에서 `a` 키를 누르면 AUTO_RUN 상태로 전환된다. (SLEEP, RUN 상태에서는 무시) |
| FR-2 | AUTO_RUN 상태에서는 키 조작이 없어도 소년이 바라보는 방향으로 계속 이동한다. |
| FR-3 | AUTO_RUN 상태의 이동 속도는 일반 RUN 상태보다 빠르고, 소년은 일반 크기보다 확대되어 그려진다. |
| FR-4 | 화면 좌우측 끝에 닿으면 자동으로 방향을 바꾸고, 바라보는 방향(애니메이션)도 함께 바뀐다. |
| FR-5 | AUTO_RUN 상태에서 **5초 이상 경과**하면 IDLE 상태로 돌아간다. 이때 크기·속도는 원래대로 돌아온다. |
| FR-6 | AUTO_RUN 상태에서 방향키(←/→)를 누르면 자동 무적 런이 취소되고, **눌린 방향**으로 움직이는 일반 RUN 상태가 된다. |
| FR-7 | FR-6으로 RUN 상태가 된 뒤에는 기존 규칙과 동일하게 동작한다. (방향키를 떼면 IDLE) |
| FR-8 | `AutoRun` 상태 클래스를 추가하여 구현한다. AUTO_RUN 상태의 진입/이탈/갱신/그리기 로직은 모두 이 클래스에 둔다. |
### 3.2 비기능 요구사항

- 기존 IDLE / SLEEP / RUN 동작은 변경되지 않아야 한다.
- 기존 코드 스타일(한글 주석, 상수는 클래스 속성)을 따른다.
- 커밋 메시지는 한글로 작성하고, 구현 과정이 단계별로 드러나도록 나누어 커밋한다.

## 4. 상태 전이 설계

변경 후 전이 표 (굵게 표시된 부분이 추가분):

| 트리거 | 출발 상태 | 도착 상태 | 설명 |
|---|---|---|---|
| `time_out` | IDLE, **AUTO_RUN** | **출발 상태에 따라 다름** | IDLE → SLEEP, **AUTO_RUN → IDLE** (각각 5초 경과) |
| `space_down` | SLEEP | IDLE | SPACE 키 누름 |
| `arrow_down(dir)` | IDLE, SLEEP, **AUTO_RUN** | RUN | 방향키 누름 |
| `arrow_up` | RUN | IDLE | 방향키 뗌 |
| **`a_down`** | **IDLE** | **AUTO_RUN** | **`a` 키 누름** |

`transitions`에서는 트리거 이름이 같아도 출발 상태별로 전이를 따로 정의할 수 있으므로, `time_out`을 두 줄로 정의한다.

```python
{'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},
{'trigger': 'time_out', 'source': 'AUTO_RUN', 'dest': 'IDLE'},
{'trigger': 'arrow_down', 'source': ['IDLE', 'SLEEP', 'AUTO_RUN'], 'dest': 'RUN'},
{'trigger': 'a_down', 'source': 'IDLE', 'dest': 'AUTO_RUN'},
```

```
                 time_out(5초)                 a_down
      SLEEP <─────────────────── IDLE ─────────────────────> AUTO_RUN
        │   ───────────────────> ▲  ▲ <──────────────────────  │
        │       space_down       │       time_out(5초)         │
        │                        │ arrow_up                    │ arrow_down(dir)
        │                        │                             ▼
        └──── arrow_down ───────> RUN <────────────────────────┘
```

- AUTO_RUN 상태에서 `arrow_up`, `space_down`, `a_down`은 무시된다.
- AUTO_RUN에서 5초가 지나면 SLEEP이 아니라 IDLE로 돌아가며, IDLE 진입 시 IDLE 5초 타이머가 새로 시작된다.

## 5. 상세 설계

### 5.1 AutoRun 상태 클래스

AUTO_RUN 상태의 로직은 별도 클래스 `AutoRun`에 둔다. `Boy`는 AUTO_RUN 상태일 때 이 클래스에 처리를 맡긴다.

```python
class AutoRun:
    SPEED = 10      # 자동 무적 런 이동 속도 (RUN의 2배)
    SCALE = 2       # 자동 무적 런 확대 배율
    DURATION = 5    # 자동 무적 런 지속 시간(초)

    def __init__(self, boy):
        self.boy = boy

    def enter(self):    # 시작 시간 기록, 바라보는 방향으로 이동 시작
    def exit(self):     # dir = 0 으로 초기화
    def do(self):       # 프레임 증가, 이동, 양끝 방향 전환, 5초 경과 시 time_out
    def draw(self):     # RUN 애니메이션을 SCALE 배로 확대해 그림
```

`Boy`와의 연결:

```python
# Boy.__init__
self.auto_run = AutoRun(self)

# transitions 콜백에서 상태 클래스 호출
def on_enter_AUTO_RUN(self):
    self.auto_run.enter()

def on_exit_AUTO_RUN(self):
    self.auto_run.exit()

# update() / draw() 분기
elif self.state == 'AUTO_RUN':
    self.auto_run.do()      # draw()에서는 self.auto_run.draw()
```

### 5.2 AutoRun 동작 상세

| 메서드 | 동작 |
|---|---|
| `enter()` | `start_time = get_time()`, `boy.dir = boy.face_dir` |
| `do()` | ① 프레임 증가 ② `boy.x += boy.dir * SPEED` ③ 좌우 끝 판정 후 방향 반전 ④ `get_time() - start_time > DURATION`이면 `boy.time_out()` |
| `draw()` | RUN 애니메이션 시트 행(오른쪽 100, 왼쪽 0)을 `100 * SCALE` 크기로 그림 |
| `exit()` | `boy.dir = 0` (방향키로 나갈 때는 이후 `on_enter_RUN(dir)`이 새 방향 설정) |

크기·속도는 `AutoRun`의 상수로만 적용되므로, 상태를 벗어나면(IDLE/RUN) 자동으로 원래 크기·속도로 돌아온다.

### 5.3 좌우 끝 판정

확대된 크기를 고려하여 판정 여백을 배율만큼 늘린다.

```python
margin = 25 * AutoRun.SCALE
if boy.x > get_canvas_width() - margin:   # 오른쪽 끝
    boy.x = get_canvas_width() - margin
    boy.dir = boy.face_dir = -1
elif boy.x < margin:                      # 왼쪽 끝
    boy.x = margin
    boy.dir = boy.face_dir = 1
```

### 5.4 확대 시 위치 보정

`clip_draw(left, bottom, w, h, x, y, dw, dh)`로 확대해 그린다. 중심 기준으로 확대되므로 그대로 그리면
발이 땅 아래로 내려간다. 발 위치가 유지되도록 y 좌표를 `(SCALE - 1) * 50`만큼 올려서 그린다.

```python
size = 100 * AutoRun.SCALE
y = boy.y + (AutoRun.SCALE - 1) * 50
boy.image.clip_draw(boy.frame * 100, 100, 100, 100, boy.x, y, size, size)
```

### 5.5 입력 처리

`handle_event`에 `a` 키 처리를 추가하고, `pico2d`에서 `SDLK_a`를 import 한다.

```python
elif event.key == SDLK_a:
    self.a_down()
```

## 6. 구현 및 커밋 계획

구현 과정이 보이도록 아래 단위로 나누어 커밋한다. (메시지는 한글)

| 순서 | 작업 내용 | 커밋 메시지 예시 |
|---|---|---|
| 1 | PRE_PRD, PRD 문서 추가 | `자동 무적 런 기능 개발 문서 작성` |
| 2 | `AutoRun` 상태 클래스 뼈대 추가, `AUTO_RUN` 상태 및 `a_down` 전이, `a` 키 입력 처리 | `AutoRun 상태 클래스와 a키 전이 추가` |
| 3 | 자동 이동 및 좌우 끝 자동 방향 전환 구현 | `자동 무적 런 이동 및 양끝 방향 전환 구현` |
| 4 | 이동 속도 증가 및 크기 확대 적용 | `자동 무적 런 속도 증가 및 크기 확대 적용` |
| 5 | 5초 경과 시 IDLE 복귀 | `자동 무적 런 5초 경과 시 IDLE 복귀 구현` |
| 6 | AUTO_RUN에서 방향키 입력 시 RUN 상태로 복귀 | `방향키 입력 시 자동 무적 런 취소 후 RUN 복귀` |
## 7. 테스트 시나리오 (인수 조건)

| # | 시나리오 | 기대 결과 |
|---|---|---|
| T-1 | IDLE에서 `a` 누름 | 소년이 커지고 바라보던 방향으로 빠르게 달리기 시작 |
| T-2 | AUTO_RUN 중 아무 키도 누르지 않음 | 5초 동안 계속 좌우로 이동 |
| T-3 | AUTO_RUN 중 오른쪽/왼쪽 끝 도달 | 화면 밖으로 나가지 않고 반대 방향으로 전환, 애니메이션 방향도 전환 |
| T-4 | AUTO_RUN 진입 후 5초 경과 | IDLE 상태로 복귀, 원래 크기로 제자리 IDLE 애니메이션 |
| T-5 | T-4 후 다시 5초 경과 | 기존 규칙대로 SLEEP 전환 |
| T-6 | AUTO_RUN 중 `→` 누름 | 원래 크기·속도로 오른쪽 RUN |
| T-7 | AUTO_RUN 중 `←` 누름 | 원래 크기·속도로 왼쪽 RUN |
| T-8 | T-6/T-7 후 방향키 뗌 | IDLE 상태로 전환 |
| T-9 | SLEEP 또는 RUN에서 `a` 누름 | 무시됨 (상태 변화 없음) |
| T-10 | 확대 상태의 소년 | 발이 땅(잔디) 위에 유지됨 |
| T-11 | 기존 동작 (IDLE→SLEEP, SPACE 기상, 방향키 RUN) | 변경 전과 동일 |
## 8. 범위 외

- 무적 판정(충돌, 피격 등)은 현재 게임에 적용 대상이 없으므로 구현하지 않는다. "무적"은 상태 명칭으로만 사용한다.
- IDLE / SLEEP / RUN 상태를 클래스로 바꾸는 리팩터링은 하지 않는다. (이번 범위는 AutoRun 상태 클래스 추가)
- 별도 이펙트/사운드는 포함하지 않는다.
