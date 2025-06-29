graph [
  directed 1
  node [
    id 0
    label "pipe_148_7_9"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/date"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/xmldb"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 0
  ]
]
