graph [
  directed 1
  node [
    id 0
    label "file{path:/var/run/rgdb.xml.gz}"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/cp"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/bin/gunzip"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/bin/gzip"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/usr/sbin/devconf"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 0
    target 4
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
