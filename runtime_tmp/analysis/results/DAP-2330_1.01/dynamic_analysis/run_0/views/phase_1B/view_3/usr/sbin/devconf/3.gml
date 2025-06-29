graph [
  directed 1
  node [
    id 0
    label "device{path:/dev/mtdblock/2}"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/devconf"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 1
    target 0
  ]
]
