graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "/usr/sbin/devconf"
    start_time "1688562161145"
    score 1.1
    is_proprietary 1
  ]
  node [
    id 1
    label "/bin/tar"
    start_time "1688562512437"
    score 0.44999999999999996
    is_proprietary 0
  ]
  node [
    id 2
    label "/bin/gzip"
    start_time "1688562161038"
    score 0.5
    is_proprietary 0
  ]
  edge [
    source 0
    target 0
    key 0
    edge_name "device{path:/dev/mtdblock/2}"
    score 0.15
    time "1688562150756"
  ]
  edge [
    source 0
    target 0
    key 1
    edge_name "device{path:/dev/mtdblock/5}"
    score 0.15
    time "1688562175613"
  ]
  edge [
    source 1
    target 2
    key 0
    edge_name "pipe_4419_4_5"
    score 0.0
    time "1688562512509"
  ]
  edge [
    source 2
    target 0
    key 0
    edge_name "file{path:/var/run/rgdb.xml.gz}"
    score 0.5
    time "1688562161158"
  ]
]
