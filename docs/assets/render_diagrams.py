"""Regenerate exact, self-contained SVG diagrams with Python's standard library."""

# SVG markup keeps its native line layout.
# ruff: noqa: E501
from html import escape
from pathlib import Path

OUT = Path(__file__).parent
INK = "#153c39"
MUTED = "#526f6c"
MINT = "#218976"
BLUE = "#6383bc"


def text(x, y, value, size=24, weight=400, color=INK, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>'


def line(path, label=None, lx=0, ly=0, dashed=False):
    color = BLUE if dashed else MINT
    dash = ' stroke-dasharray="9 8"' if dashed else ""
    svg = f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{"blue" if dashed else "arrow"})"{dash}/>'
    if label:
        svg += text(lx, ly, label, 20, 500, color, "middle")
    return svg


def icon(kind, x, y):
    shapes = {
        "api": '<rect x="3" y="5" width="42" height="31" rx="6"/><path d="M14 15l-5 6 5 6m20-12 5 6-5 6M19 42h10M24 36v6"/>',
        "runtime": '<path d="M9 12h30M9 24h30M9 36h30"/><circle cx="17" cy="12" r="4" fill="#e1f5ee"/><circle cx="32" cy="24" r="4" fill="#e1f5ee"/><circle cx="20" cy="36" r="4" fill="#e1f5ee"/>',
        "agent": '<rect x="5" y="12" width="38" height="29" rx="10"/><path d="M24 5v7M1 22v10m46-10v10"/><circle cx="16" cy="25" r="2" fill="#218976"/><circle cx="32" cy="25" r="2" fill="#218976"/><path d="M18 33h12"/>',
        "tools": '<path d="M9 14V8h30v6M4 17h40v25H4zM4 27h40M20 24h8v7h-8z"/>',
        "db": '<ellipse cx="24" cy="9" rx="19" ry="7"/><path d="M5 9v28c0 9 38 9 38 0V9M5 22c0 9 38 9 38 0"/>',
        "model": '<path d="M24 3l7 14 14 7-14 7-7 14-7-14-14-7 14-7z"/>',
        "service": '<rect x="7" y="3" width="34" height="42" rx="6"/><path d="M15 14h18M15 24h18M15 34h10"/>',
        "check": '<path d="M8 25l10 10L40 12"/>',
    }
    return f'<g transform="translate({x} {y})" fill="none" stroke="{MINT}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">{shapes[kind]}</g>'


def card(x, y, w, title, subtitle, detail, kind, tag="", h=185):
    svg = (
        f'<rect x="{x}" y="{y + 6}" width="{w}" height="{h}" rx="24" fill="#dbe9e3" opacity=".7"/>'
    )
    svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="white" stroke="#cce0d7" stroke-width="1.5"/>'
    svg += f'<rect x="{x + 22}" y="{y + 22}" width="64" height="64" rx="19" fill="url(#tile)"/>'
    svg += icon(kind, x + 30, y + 29)
    if tag:
        svg += text(x + w - 22, y + 42, tag, 17, 700, MINT, "end")
    svg += text(x + 22, y + 119, title, 28, 700)
    svg += text(x + 22, y + 151, subtitle, 20, 400, MUTED)
    if detail:
        svg += text(x + 22, y + 176, detail, 17, 400, MUTED)
    return svg


def canvas(title, sub, content, height, desc, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#f4faf5"/><stop offset="1" stop-color="#eef5fa"/></linearGradient>
<linearGradient id="tile" x2="1" y2="1"><stop stop-color="#c4f0df"/><stop offset="1" stop-color="#eefbf5"/></linearGradient>
<marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="{MINT}" stroke-width="1.5"/></marker>
<marker id="blue" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="{BLUE}" stroke-width="1.5"/></marker>
</defs>
<rect width="1440" height="{height}" rx="30" fill="url(#bg)"/>
<g font-family="Noto Sans KR, Noto Sans CJK KR, Arial, sans-serif">
{text(64, 60, "AGENT STARTER TEMPLATE / " + label, 18, 700, MINT)}
{text(64, 121, title, 44, 700)}
{text(64, 163, sub, 23, 400, MUTED)}
{content}
</g></svg>'''


def architecture(ko):
    def t(en, kr):
        return kr if ko else en

    s = line("M380 317H470", "HTTP", 425, 298)
    s += line("M650 410V480", t("start / resume", "실행 / 재개"), 750, 452)
    s += line("M480 582H390", t("calls", "호출"), 435, 560)
    s += line("M820 620H970", t("executes", "실행"), 896, 600)
    s += line("M820 535H889V320H970", t("checkpoints", "상태 저장"), 894, 296, True)
    s += line("M1150 675V745", t("service call", "서비스 호출"), 1252, 718)
    s += card(
        70,
        225,
        310,
        "FastAPI",
        t("Request validation + token", "요청 검증 + 선택형 토큰"),
        "api/",
        "api",
        "01",
    )
    s += card(
        480,
        225,
        340,
        t("Run coordinator", "실행 조정"),
        t("Thread lock + time budget", "대화별 동시 실행 차단 · 시간 제한"),
        "services/runtime.py",
        "runtime",
        "02",
    )
    s += card(
        980,
        225,
        370,
        "SQLite",
        t("Messages + saved graph state", "메시지 · 그래프 상태 저장"),
        "persistence/",
        "db",
        "STATE",
    )
    s += card(
        480,
        490,
        340,
        "LangGraph",
        t("Model decision + tool loop", "모델 판단 · 도구 실행 반복"),
        "agent/",
        "agent",
        "03",
    )
    s += card(
        70,
        490,
        310,
        t("Model adapter", "모델 어댑터"),
        "Demo / Anthropic",
        "integrations/",
        "model",
        "MODEL",
    )
    s += card(
        980,
        490,
        370,
        t("Typed tools", "타입이 정의된 도구"),
        t("Allowlist + validation + timeout", "허용 목록 · 입력 검증 · 시간 제한"),
        "tools/ + policies/",
        "tools",
        "04",
    )
    s += card(
        980,
        755,
        370,
        t("Business services", "업무 서비스"),
        t("Policy search / request status", "문서 검색 / 요청 상태 조회"),
        t("Fictional data · read-only", "가상 데이터 · 읽기 전용"),
        "service",
        "05",
    )
    s += text(
        70,
        808,
        t(
            "The model chooses. The application executes.",
            "모델은 선택하고, 애플리케이션이 실행합니다.",
        ),
        28,
        700,
    )
    s += text(
        70,
        850,
        t(
            "Tools call services; business rules stay out of prompts.",
            "도구는 서비스를 호출하고, 업무 규칙은 코드로 관리합니다.",
        ),
        22,
        400,
        MUTED,
    )
    s += text(
        70,
        887,
        t(
            "SQLite checkpoints preserve completed graph steps.",
            "완료된 그래프 단계는 SQLite 체크포인트로 보존합니다.",
        ),
        22,
        400,
        MUTED,
    )
    s += line("M72 966H132") + text(148, 974, t("Execution", "실행 호출"), 19, 400, MUTED)
    s += line("M330 966H390", dashed=True) + text(
        405, 974, t("Checkpoint writes", "체크포인트 저장"), 19, 400, MUTED
    )
    s += text(
        1368,
        974,
        t("Single tenant · one worker · read-only demo", "단일 테넌트 · 워커 1개 · 읽기 전용 데모"),
        18,
        400,
        MUTED,
        "end",
    )
    return canvas(
        t("How the pieces fit together", "구성요소가 어떻게 연결될까요?"),
        t(
            "A small service with clear responsibilities.",
            "각 구성요소의 역할을 분리한 작은 에이전트 서비스입니다.",
        ),
        s,
        1020,
        t(
            "FastAPI calls the coordinator, which starts or resumes the graph. The graph calls the model adapter and typed tools, and writes checkpoints to SQLite. Tools call business services.",
            "FastAPI에서 실행 조정을 거쳐 그래프를 실행합니다. 그래프는 모델과 도구를 호출하고 SQLite에 체크포인트를 저장합니다. 도구가 업무 서비스를 호출합니다.",
        ),
        "ARCHITECTURE",
    )


def flow(ko):
    def t(en, kr):
        return kr if ko else en

    s = line("M420 306H525") + text(472, 286, t("input", "입력"), 19, 500, MINT, "middle")
    s += line("M910 306H1005")
    s += line("M1200 400V484")
    # Branch card is deliberately rectangular so the text stays legible at README width.
    s += line("M1005 575H910", t("Yes", "예"), 958, 555)
    s += line("M535 575H420", t("results", "결과"), 478, 555)
    s += line("M240 485V446H705V406", t("next decision", "다음 판단"), 465, 431)
    s += line("M1200 670V758", t("No", "아니요"), 1232, 720)
    s += card(
        65,
        215,
        355,
        t("1. Receive a message", "1. 요청 받기"),
        t("Validate input and thread", "입력과 대화 상태 검증"),
        "POST /v1/runs",
        "api",
    )
    s += card(
        535,
        215,
        375,
        t("2. Ask the model", "2. 모델에 판단 요청"),
        t("Check model-call budget", "모델 호출 횟수 확인"),
        t("Prompt + conversation history", "프롬프트 + 대화 기록"),
        "agent",
    )
    s += card(
        1015,
        215,
        360,
        t("3. Read the decision", "3. 판단 결과 확인"),
        t("Answer or tool calls", "최종 응답 또는 도구 호출"),
        t("Demo rules / real model", "데모 규칙 / 실제 모델"),
        "model",
    )
    s += card(
        1015,
        490,
        360,
        t("Tools requested?", "도구 호출이 필요한가요?"),
        t("Branch on the model output", "모델 출력에 따라 분기"),
        "",
        "runtime",
    )
    s += card(
        535,
        490,
        375,
        t("4. Execute tools", "4. 도구 실행"),
        t("Budget + allowlist + schema", "횟수 · 허용 목록 · 입력 검증"),
        t("Read-only calls with timeouts", "시간 제한 내 읽기 전용 실행"),
        "tools",
    )
    s += card(
        65,
        490,
        355,
        t("5. Add observations", "5. 결과를 대화에 추가"),
        t("Return results to the model", "실행 결과를 모델에 전달"),
        t("Checkpoint each graph step", "각 그래프 단계 체크포인트 저장"),
        "db",
    )
    s += card(
        1015,
        765,
        360,
        t("6. Return an answer", "6. 최종 응답 반환"),
        t("Output + status + usage", "응답 + 상태 + 사용량"),
        "completed",
        "check",
    )
    s += '<rect x="65" y="764" width="845" height="191" rx="24" fill="#e2efe9"/>'
    s += text(90, 807, t("EXAMPLE: 12 * 7", "예시: 12 * 7"), 21, 700, MINT)
    s += text(
        90,
        850,
        t("calculate(multiply, 12, 7) returns 84.0", "calculate(multiply, 12, 7) → 84.0"),
        28,
        700,
    )
    s += text(
        90,
        890,
        t(
            "The result goes back to the model for the final response.",
            "실행 결과를 모델에 전달한 뒤 최종 응답을 만듭니다.",
        ),
        22,
        400,
        MUTED,
    )
    s += text(
        90,
        926,
        t(
            "Demo mode uses two scripted model calls; no paid API.",
            "데모는 규칙 기반 모델 호출 2회로 처리하며 API 비용이 없습니다.",
        ),
        20,
        400,
        MUTED,
    )
    s += text(
        65,
        1006,
        t(
            "Limits stop the loop. A timeout returns 504; inspect the thread before resuming.",
            "한도에 도달하면 반복을 종료합니다. 시간 초과는 504를 반환하며 대화 상태 확인 후 재개합니다.",
        ),
        21,
        500,
        MUTED,
    )
    s += text(
        65,
        1041,
        t(
            "Main success path shown. Model errors return model_error; tool errors are observations.",
            "정상 흐름 중심의 그림입니다. 모델 오류는 model_error, 도구 오류는 실행 결과로 전달합니다.",
        ),
        19,
        400,
        MUTED,
    )
    return canvas(
        t("From a message to a useful result", "요청 한 건은 어떻게 처리될까요?"),
        t(
            "Follow the tool loop, then return a final answer.",
            "필요한 도구를 실행하고 결과를 확인한 뒤 최종 응답을 만듭니다.",
        ),
        s,
        1080,
        t(
            "Receive a message, ask the model, and inspect its decision. Tool calls are executed and their observations loop back to the model. If no tool is requested, return the answer.",
            "요청을 받고 모델에 판단을 요청합니다. 도구 호출이 있으면 실행 결과를 모델에 다시 전달합니다. 도구 호출이 없으면 최종 응답을 반환합니다.",
        ),
        "REQUEST FLOW",
    )


if __name__ == "__main__":
    for locale in ("en", "ko"):
        for name, build in [("architecture", architecture), ("request-flow", flow)]:
            path = OUT / f"{name}.{locale}.svg"
            path.write_text(build(locale == "ko"), encoding="utf-8")
            print(path.name)
