graph [
  directed 1
  node [
    id 0
    label "device{path:/dev/mtdblock/5}"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/echo"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/devconf"
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
    source 2
    target 0
  ]
]
