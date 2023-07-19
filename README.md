CampFire is a web application that turns iRule log files into flame graphs.
<br>More information about [CampFire can be found here](https://www.youtube.com/live/ttW701tqXRM?feature=share&t=2789).

## Run CampFire in Local Environment
Prerequisites: Docker, socat*
<br>[Information about Docker](https://docs.docker.com/docker-for-mac/install/)
<br>[Information about socat](https://www.cyberciti.biz/faq/linux-unix-tcp-port-forwarding/)

Initial `make run` will take about ~5 minutes.
#### macOS Environment:
*If you have [brew](https://brew.sh/) installed: `brew install socat`

1. Navigate to the directory you want to run the program in
2. `git clone https://github.com/f5devcentral/campfire.git` or download file
3. `cd campfire`
4. `make run`

#### VM Linux Environment:

1. Navigate to the directory you want to run the program in
2. `git clone https://github.com/f5devcentral/campfire.git`
3. `cd campfire`
4. `make run`

Additional resources: [FlameGraphs](http://www.brendangregg.com/flamegraphs.html)
