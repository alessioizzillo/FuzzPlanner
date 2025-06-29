graph [
  directed 1
  node [
    id 0
    label "pipe_3435_4_5"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/rgdb"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/submit"
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
