#!/bin/bash

while true; do
    # Listen on port 3000 and accept incoming connections
    { 
        echo -ne "HTTP/1.1 100 Continue\r\n\r\n"; # Send 100 Continue
        sleep 1; # Simulate a delay for demonstration purposes
        echo -ne "HTTP/1.1 200 OK\r\nContent-Length: 8\r\nContent-Type: text/plain\r\n\r\nSuccess!\r\n";
    } | nc -l -p 3000 > /tmp/http_request

    cat /tmp/http_request
done
