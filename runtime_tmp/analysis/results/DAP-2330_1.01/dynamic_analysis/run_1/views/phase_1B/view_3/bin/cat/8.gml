graph [
  directed 1
  node [
    id 0
    label "file{path:/var/run/stunnel.pid}"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/stunnel"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/bin/cat"
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
