graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "/bin/gzip"
    start_time "1688562161038"
    score 0.5
    is_proprietary 0
  ]
  node [
    id 1
    label "/usr/sbin/devconf"
    start_time "1688562161145"
    score 0.9500000000000001
    is_proprietary 1
  ]
  edge [
    source 0
    target 1
    key 0
    edge_name "file{path:/var/run/rgdb.xml.gz}"
    score 0.5
    time "1688562161158"
  ]
  edge [
    source 1
    target 1
    key 0
    edge_name "device{path:/dev/mtdblock/2}"
    score 0.15
    time "1688562150756"
  ]
  edge [
    source 1
    target 1
    key 1
    edge_name "device{path:/dev/mtdblock/5}"
    score 0.15
    time "1688562175613"
  ]
]
