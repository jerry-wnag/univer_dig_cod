ClearAll[makeInputCell];
SetAttributes[makeInputCell, HoldAllComplete];

makeInputCell[expr_] :=
  Cell[
    BoxData[ToBoxes[Unevaluated[expr], StandardForm]],
    "Input"
  ];

builderDirectory = DirectoryName[$InputFileName];
If[!StringQ[builderDirectory] || builderDirectory === "",
  builderDirectory = Directory[]
];

notebookPath = FileNameJoin[{builderDirectory, "TCCT_S71_Local.nb"}];

notebook = Notebook[
  {
    Cell["TCCT S71 本地运行与可视化", "Title"],
    Cell[
      "Blind Topology Transfer Checkpoint - 从 111 页 PDF 恢复。首次使用请按顺序选中每个输入单元，按 Shift+Enter 运行；也可以在 Evaluation 菜单中选择 Evaluate Notebook。",
      "Text"
    ],

    Cell["1. 环境检查", "Section"],
    makeInputCell[
      <|
        "WolframVersion" -> $Version,
        "SystemID" -> $SystemID,
        "ProcessorCount" -> $ProcessorCount,
        "KernelCount" -> $KernelCount
      |>
    ],

    Cell["2. 载入昨晚的完整 S59-S71 代码", "Section"],
    Cell[
      "这一格会执行恢复出的 142 个输入单元。搜索阶段可能需要一些时间；完成后会显示总耗时。",
      "Text"
    ],
    makeInputCell[
      With[
        {
          source = FileNameJoin[
            {NotebookDirectory[], "TCCT_S71_recovered_full.wl"}
          ]
        },
        Print["正在载入并运行 S59-S71，请稍候..."];
        loadTiming71 = AbsoluteTiming[Get[source]][[1]];
        Print[
          Row[
            {
              "S59-S71 运行完成，用时 ",
              NumberForm[loadTiming71, {Infinity, 2}],
              " 秒"
            }
          ]
        ];
      ]
    ],

    Cell["3. S71 检查点结果", "Section"],
    makeInputCell[Dataset[{blindCert71}]],
    makeInputCell[
      BarChart[
        candidateScores71,
        ChartLabels -> Placed[Range[Length[candidateScores71]], Below],
        PlotRange -> {0, 32},
        AxesLabel -> {"Candidate", "ParallelIn score"},
        PlotLabel -> "Five SharedMerge-perfect candidates on ParallelIn",
        ImageSize -> Large
      ]
    ],

    Cell["4. 图结构对照", "Section"],
    Cell[
      "下面把同一个 Continue case 在基础 S59 与 ParallelIn 盲拓扑中的结构并排显示。",
      "Text"
    ],
    makeInputCell[
      With[
        {
          base = Case59[2, 1, "Continue"],
          parallel = Case71[2, 1, "Continue"]
        },
        Grid[
          {
            {
              Style["S59 base", Bold, 14],
              Style["ParallelIn blind topology", Bold, 14]
            },
            {
              Graph[
                base[[1, 1]],
                GraphLayout -> "LayeredDigraphEmbedding",
                VertexLabels -> None,
                VertexSize -> Tiny,
                ImageSize -> 500
              ],
              Graph[
                parallel[[1, 1]],
                GraphLayout -> "LayeredDigraphEmbedding",
                VertexLabels -> None,
                VertexSize -> Tiny,
                ImageSize -> 500
              ]
            }
          },
          Frame -> All,
          Spacings -> {2, 1}
        ]
      ]
    ],

    Cell["5. 冻结模型", "Section"],
    makeInputCell[
      frozen71 = <|
        "K" -> 5,
        "Params" -> {0, -1, 1, -1, -1, 0},
        "Policy" -> {1, 4}
      |>
    ],
    Cell[
      "S71 是封存检查点。后续 S72 请另建 Notebook，不要在本文件中修改冻结参数或用新拓扑重新选择模型。",
      "Text"
    ]
  },
  WindowTitle -> "TCCT S71 - Blind Topology Transfer",
  Saveable -> True,
  StyleDefinitions -> "Default.nb"
];

Export[notebookPath, notebook, "NB"];
Print["Created notebook: " <> notebookPath];
