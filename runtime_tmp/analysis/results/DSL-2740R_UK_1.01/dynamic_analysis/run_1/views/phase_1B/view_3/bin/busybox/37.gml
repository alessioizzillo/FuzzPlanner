graph [
  directed 1
  node [
    id 0
    label "file{path:/usr/etc/l7-protocols/msnmessenger.pat}"
    kind "channel"
  ]
  node [
    id 1
    label "<border>"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/bin/busybox"
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
