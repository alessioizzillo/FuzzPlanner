graph [
  directed 1
  node [
    id 0
    label "file{path:/var/run/http-loop.sh}"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/xmldb"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/bin/sh"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/sbin/atp"
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
]
