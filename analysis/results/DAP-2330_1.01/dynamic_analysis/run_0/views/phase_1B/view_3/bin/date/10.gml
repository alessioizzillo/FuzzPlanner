graph [
  directed 1
  node [
    id 0
    label "pipe_148_8_9"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/devdata"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/xmldb"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/usr/bin/uptime"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/bin/date"
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
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 0
  ]
]
