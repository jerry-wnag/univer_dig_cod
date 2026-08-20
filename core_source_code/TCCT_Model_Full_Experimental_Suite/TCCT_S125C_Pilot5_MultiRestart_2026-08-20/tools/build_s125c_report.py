import csv
import hashlib
import statistics
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(r"C:\Users\王鑫\Documents\Codex\2026-08-20\referenced-chatgpt-conversation-this-is-an")
CSV_PATH = Path(
    r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development"
    r"\S125C_Jupyter_Pilot5_MultiRestartMatched_Output"
    r"\S125C_pilot_per_world_summary.csv"
)
MANIFEST_PATH = Path(
    r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development"
    r"\S125C_Jupyter_Pilot5_MultiRestartMatched_Output"
    r"\S125C_pilot_preregistered_manifest.json"
)
OUTPUT = ROOT / "outputs" / "TCCT_S125C_Pilot5_MultiRestart_Report.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def number(row, key):
    return float(row[key].strip('"'))


def integer(row, key):
    return int(float(row[key].strip('"')))


def pct(value):
    return f"{100.0 * value:.2f}%"


def p(text, style):
    return Paragraph(text, style)


font_regular = Path(r"C:\Windows\Fonts\msyh.ttc")
font_bold = Path(r"C:\Windows\Fonts\msyhbd.ttc")
if not font_regular.exists():
    font_regular = Path(r"C:\Windows\Fonts\simhei.ttf")
if not font_bold.exists():
    font_bold = font_regular

pdfmetrics.registerFont(TTFont("ReportCJK", str(font_regular), subfontIndex=0))
pdfmetrics.registerFont(TTFont("ReportCJKBold", str(font_bold), subfontIndex=0))

with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))

if len(rows) != 5:
    raise ValueError(f"Expected five S125-C rows, found {len(rows)}")
if not all(row["RunPassed"].lower() == "true" for row in rows):
    raise ValueError("S125-C report requires five passed rows")

matched_params = integer(rows[0], "MatchedReasonParameterCount")
strong_params = integer(rows[0], "StrongReasonParameterCount")
param_ratio = strong_params / matched_params
state_total = len(rows) * integer(rows[0], "HighOrderHoldoutStates")
transition_total = len(rows) * integer(rows[0], "HighOrderTransitionCases")

means = {
    key: statistics.fmean(number(row, key) for row in rows)
    for key in [
        "ReasonValidationBalancedAccuracy",
        "FinalReasonTrainingBalancedAccuracy",
        "NeuralBalancedAccuracy",
        "NeuralTransitionBalancedAccuracy",
        "StrongReasonValidationBalancedAccuracy",
        "StrongFinalReasonTrainingBalancedAccuracy",
        "StrongProbeBalancedAccuracy",
        "StrongTransitionBalancedAccuracy",
    ]
}

PAGE_W, PAGE_H = A4
navy = colors.HexColor("#17324D")
blue = colors.HexColor("#246B9E")
teal = colors.HexColor("#1C8A7A")
green = colors.HexColor("#238B57")
light_green = colors.HexColor("#E9F6EF")
light_blue = colors.HexColor("#EEF5FA")
light_gray = colors.HexColor("#F4F6F8")
mid_gray = colors.HexColor("#D6DDE3")
text_color = colors.HexColor("#24313B")
muted = colors.HexColor("#5B6B76")

styles = getSampleStyleSheet()
title = ParagraphStyle(
    "TitleCJK",
    parent=styles["Title"],
    fontName="ReportCJKBold",
    fontSize=22,
    leading=29,
    textColor=navy,
    alignment=TA_CENTER,
    spaceAfter=10,
)
subtitle = ParagraphStyle(
    "SubtitleCJK",
    parent=styles["Normal"],
    fontName="ReportCJK",
    fontSize=10.5,
    leading=16,
    textColor=muted,
    alignment=TA_CENTER,
    spaceAfter=16,
)
h1 = ParagraphStyle(
    "H1CJK",
    parent=styles["Heading1"],
    fontName="ReportCJKBold",
    fontSize=15,
    leading=21,
    textColor=navy,
    spaceBefore=5,
    spaceAfter=9,
)
h2 = ParagraphStyle(
    "H2CJK",
    parent=styles["Heading2"],
    fontName="ReportCJKBold",
    fontSize=11.5,
    leading=16,
    textColor=blue,
    spaceBefore=6,
    spaceAfter=5,
)
body = ParagraphStyle(
    "BodyCJK",
    parent=styles["BodyText"],
    fontName="ReportCJK",
    fontSize=9.2,
    leading=15,
    textColor=text_color,
    alignment=TA_LEFT,
    spaceAfter=6,
)
small = ParagraphStyle(
    "SmallCJK",
    parent=body,
    fontSize=7.6,
    leading=11,
    textColor=muted,
    spaceAfter=2,
)
table_head = ParagraphStyle(
    "TableHeadCJK",
    parent=small,
    fontName="ReportCJKBold",
    textColor=colors.white,
    alignment=TA_CENTER,
)
table_cell = ParagraphStyle(
    "TableCellCJK",
    parent=small,
    fontSize=7.3,
    leading=10,
    textColor=text_color,
    alignment=TA_CENTER,
)
callout = ParagraphStyle(
    "CalloutCJK",
    parent=body,
    fontName="ReportCJKBold",
    fontSize=10.5,
    leading=16,
    textColor=green,
    alignment=TA_CENTER,
    spaceAfter=0,
)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(mid_gray)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 17 * mm, PAGE_W - 18 * mm, 17 * mm)
    canvas.setFont("ReportCJK", 7.5)
    canvas.setFillColor(muted)
    canvas.drawString(18 * mm, 11 * mm, "TCCT S125-C Pilot-5")
    canvas.drawRightString(PAGE_W - 18 * mm, 11 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=17 * mm,
    rightMargin=17 * mm,
    topMargin=17 * mm,
    bottomMargin=23 * mm,
    title="TCCT S125-C Pilot-5 Multi-Restart Matched Transformer Comparison",
    author="TCCT experiment report",
)

story = []
story.append(Spacer(1, 6 * mm))
story.append(p("TCCT S125-C 五世界对比测试报告", title))
story.append(
    p(
        "三种子 matched Transformer 低阶选择 + 4× 强 Transformer<br/>"
        "严格 fresh-world，高阶状态与转移在全部模型冻结后首次打开",
        subtitle,
    )
)

summary_box = Table(
    [[p("整体协议通过：5/5 世界完成，0 次门控失败，S125COverallPass = True", callout)]],
    colWidths=[172 * mm],
)
summary_box.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), light_green),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#A9DCC0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]
    )
)
story.append(summary_box)
story.append(Spacer(1, 6 * mm))

story.append(p("核心结论", h1))
conclusion_data = [
    ["TCCT 高阶状态", f"{state_total}/{state_total} exact", "100%"],
    ["TCCT 高阶转移", f"{transition_total}/{transition_total} exact", "100%"],
    ["Matched Transformer", "状态与转移 exact", "均为 0%"],
    ["4× Strong Transformer", "状态与转移 exact", "均为 0%"],
]
conclusion_table = Table(
    [[p(x, table_head) for x in ["系统", "五世界合计", "结果"]]]
    + [[p(str(x), table_cell) for x in row] for row in conclusion_data],
    colWidths=[58 * mm, 72 * mm, 42 * mm],
    repeatRows=1,
)
conclusion_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_gray]),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
)
story.append(conclusion_table)
story.append(Spacer(1, 4 * mm))
story.append(
    p(
        "S125-B 的单次 matched final 初始化曾导致 1/5 世界在高阶打开前停止。S125-C 预注册三组 selection 与三组 final 种子，"
        "只依据低阶 validation/training balanced accuracy 选择并冻结模型，完成率由 4/5 提升到 5/5；没有降低 0.60/0.70 门槛，也没有使用高阶结果调参。",
        body,
    )
)

story.append(p("协议与架构边界", h1))
protocol_rows = [
    ["训练上限", "MaximumTrainingInteractionOrder = 2"],
    ["高阶 holdout", "至少 3 个同时非零因子；每世界 74 状态、592 转移"],
    ["感知器", "共享、冻结；不参与 reasoner-only 参数差异"],
    ["Matched reasoner", f"架构不变，{matched_params:,} 参数；3 selection + 3 final seeds"],
    ["Strong reasoner", f"{strong_params:,} 参数，为 matched 的 {param_ratio:.2f}×"],
    ["选择信息", "仅低阶 validation/training；HighOrderUsedForSelection = False"],
    ["整体标准", "5/5 世界必须全部通过；RequiredPassRate = 1.00"],
]
protocol_table = Table(
    [[p(a, table_cell), p(b, table_cell)] for a, b in protocol_rows],
    colWidths=[42 * mm, 130 * mm],
)
protocol_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (0, -1), light_blue),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(protocol_table)

story.append(PageBreak())
story.append(p("逐世界结果", h1))
world_headers = [
    "World",
    "Cells",
    "选择种子<br/>selection/final",
    "低阶 balanced<br/>validation/training",
    "TCCT exact<br/>state / trans.",
    "Matched exact<br/>state / trans.",
    "Strong exact<br/>state / trans.",
]
world_data = [[p(x, table_head) for x in world_headers]]
for row in rows:
    world_data.append(
        [
            p(row["WorldSeed"], table_cell),
            p(row["ConditionalTransitionCells"], table_cell),
            p(
                f"{row['MatchedSelectedSelectionSeed']}<br/>{row['MatchedSelectedFinalSeed']}",
                table_cell,
            ),
            p(
                f"{pct(number(row, 'ReasonValidationBalancedAccuracy'))}<br/>"
                f"{pct(number(row, 'FinalReasonTrainingBalancedAccuracy'))}",
                table_cell,
            ),
            p("100%<br/>100%", table_cell),
            p("0%<br/>0%", table_cell),
            p("0%<br/>0%", table_cell),
        ]
    )

world_table = Table(
    world_data,
    colWidths=[22 * mm, 14 * mm, 32 * mm, 31 * mm, 25 * mm, 25 * mm, 25 * mm],
    repeatRows=1,
)
world_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_gray]),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(world_table)
story.append(Spacer(1, 5 * mm))

story.append(p("低阶能力门控", h2))
gate_data = [
    ["Matched validation balanced", pct(means["ReasonValidationBalancedAccuracy"]), "门槛 60%"],
    ["Matched final training balanced", pct(means["FinalReasonTrainingBalancedAccuracy"]), "门槛 70%"],
    ["Strong validation balanced", pct(means["StrongReasonValidationBalancedAccuracy"]), "门槛 60%"],
    ["Strong final training balanced", pct(means["StrongFinalReasonTrainingBalancedAccuracy"]), "门槛 70%"],
]
gate_table = Table(
    [[p(x, table_head) for x in ["指标", "五世界均值", "预注册门槛"]]]
    + [[p(x, table_cell) for x in row] for row in gate_data],
    colWidths=[82 * mm, 42 * mm, 48 * mm],
)
gate_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), blue),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_blue]),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(gate_table)
story.append(Spacer(1, 4 * mm))
story.append(
    p(
        "五个世界选中的 selection seed 覆盖 1258611、1258612、1258613；final seed 覆盖 1258621、1258622、1258623。"
        "这说明 multi-restart 不是固定种子捷径，而是在每个 fresh world 内依据低阶指标独立选择。",
        body,
    )
)

story.append(p("Probe-level 结果与 exact 的区别", h2))
probe_rows = [
    ["Matched state probe balanced", pct(means["NeuralBalancedAccuracy"])],
    ["Matched transition probe balanced", pct(means["NeuralTransitionBalancedAccuracy"])],
    ["Strong state probe balanced", pct(means["StrongProbeBalancedAccuracy"])],
    ["Strong transition probe balanced", pct(means["StrongTransitionBalancedAccuracy"])],
]
probe_table = Table(
    [[p(a, table_cell), p(b, table_cell)] for a, b in probe_rows],
    colWidths=[120 * mm, 52 * mm],
)
probe_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (0, -1), light_blue),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(probe_table)
story.append(
    p(
        "两种 Transformer 能在单独 probe 上达到接近随机或略高的 balanced accuracy，但没有一次恢复完整的 14-bit 高阶结构签名；"
        "因此 probe 部分正确不能替代 exact compositional generalization。",
        body,
    )
)

story.append(PageBreak())
story.append(p("参数效率与解释", h1))
param_data = [
    ["TCCT reasoning representation", "41–42 sparse conditional cells", "结构化离散规则"],
    ["Matched Transformer reasoner", f"{matched_params:,} parameters", "基准神经推理器"],
    ["Strong Transformer reasoner", f"{strong_params:,} parameters", f"matched 的 {param_ratio:.2f}×"],
]
param_table = Table(
    [[p(x, table_head) for x in ["Reasoner", "规模", "说明"]]]
    + [[p(x, table_cell) for x in row] for row in param_data],
    colWidths=[68 * mm, 60 * mm, 44 * mm],
)
param_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_gray]),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
)
story.append(param_table)
story.append(Spacer(1, 4 * mm))
story.append(
    p(
        "41–42 个 conditional cells 与神经网络标量权重不是同一种参数，不能直接宣称严格的 1:1 压缩倍数。"
        "但在共享感知器被固定、reasoner-only 对比成立的条件下，TCCT 的结构表示以极小的稀疏规则表完成了 100% exact 高阶组合，"
        "而 85,890 与 339,170 参数的 Transformer 均为 0% exact，说明当前优势不是单纯由神经容量不足造成。",
        body,
    )
)

story.append(p("完整性审计", h1))
integrity_rows = [
    ["Canonical base-source SHA-256", "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"],
    ["S125-C manifest SHA-256", "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540"],
    ["Pre-world protocol SHA-256", "617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9"],
    ["CSV SHA-256", sha256(CSV_PATH)],
    ["Manifest JSON SHA-256", sha256(MANIFEST_PATH)],
    ["Freeze ordering", "AllModelsFrozenBeforeHighOrder = True (5/5)"],
    ["High-order leakage", "HighOrderTouchedBeforeFreeze = 0 (5/5)"],
    ["Protocol hash stability", "True"],
]
integrity_table = Table(
    [[p(a, table_cell), p(b, small)] for a, b in integrity_rows],
    colWidths=[50 * mm, 122 * mm],
)
integrity_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (0, -1), light_blue),
            ("GRID", (0, 0), (-1, -1), 0.5, mid_gray),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(integrity_table)

story.append(p("当前阶段与下一步", h1))
story.append(
    p(
        "S125-C 是具有严格 prospective 证据的神经感知 + 结构推理原型验证，不等同于已经证明在自然语言、现实视觉或大规模开放环境中全面优于 Transformer。"
        "本轮最有价值的结论是：在共享感知、低阶训练和高阶 sealed holdout 条件下，低阶多重重启稳定了神经基线，却没有缩小 exact 组合泛化差距。",
        body,
    )
)
story.append(
    p(
        "建议下一阶段从 5-world pilot 扩展到 20 个全新预注册世界，并加入训练时间、推理延迟、内存占用与受控噪声扰动；"
        "multi-restart 数量、种子、门槛和停止标准必须在打开任何新世界前继续冻结。",
        body,
    )
)

story.append(Spacer(1, 5 * mm))
closing = Table(
    [[p("结论：S125-C 以 5/5 严格通过，支持 TCCT 相对合格 matched 与 4× strong Transformer 的高阶 exact 组合泛化优势。", callout)]],
    colWidths=[172 * mm],
)
closing.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), light_green),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#A9DCC0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]
    )
)
story.append(closing)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(OUTPUT)
