graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "/bin/cat"
    start_time "1688561715108"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 1
    label "/usr/script/wan_stop.sh"
    start_time "1688561712483"
    score 0.65
    is_proprietary 1
  ]
  node [
    id 2
    label "/bin/hostname"
    start_time "1688561600576"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 3
    label "/userfs/bin/radvd"
    start_time "1688561610974"
    score 1.65
    is_proprietary 1
  ]
  node [
    id 4
    label "/bin/echo"
    start_time "1688561603448"
    score 0.0
    is_proprietary 0
  ]
  edge [
    source 0
    target 1
    key 0
    edge_name "pipe_889_7_9"
    score 0.0
    time "1688561715160"
  ]
  edge [
    source 4
    target 0
    key 0
    edge_name "file{path:/var/run/nas0.pid}"
    score 0.0
    time "1688561715159"
  ]
  edge [
    source 4
    target 3
    key 0
    edge_name "virtual_file{path:/proc/sys/net/ipv6/conf/all/forwarding}"
    score 0.0
    time "1688561611038"
  ]
  edge [
    source 4
    target 2
    key 0
    edge_name "file{path:/etc/hostname}"
    score 0.0
    time "1688561600637"
  ]
]
