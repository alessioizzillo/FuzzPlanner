graph [
  directed 1
  node [
    id 0
    label "file{path:/etc/nat_pvc0/vserver0}"
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
    label "/usr/script/vserver.sh"
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
