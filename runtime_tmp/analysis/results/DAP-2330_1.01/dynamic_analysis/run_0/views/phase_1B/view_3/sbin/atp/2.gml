graph [
  directed 1
  node [
    id 0
    label "file{path:/etc/TZ}"
    kind "channel"
  ]
  node [
    id 1
    label "/sbin/httpd"
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
    label "/bin/echo"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/sbin/atp"
    kind "executable"
    listening 0
  ]
  node [
    id 5
    label "/sbin/xgi"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 0
    target 1
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
  edge [
    source 5
    target 0
  ]
]
