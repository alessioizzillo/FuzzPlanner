graph [
  directed 1
  node [
    id 0
    label "file{path:/var/etc/httpd.cfg}"
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
    label "/bin/sh"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/sbin/httpd"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 0
    target 3
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 2
    target 0
  ]
]
