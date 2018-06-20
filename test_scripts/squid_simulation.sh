

/bin/python3 -m ajustador.basic_simulation \
      --baseline=-0.07639880161359705 \
      --model=squid \
      --neuron-type=squid \
      --RA=1.000001 \
      --RM=1.0 \
      --morph-file=squid.p \
      --simtime=0.9 \
      -i=1.0e-9 \
      --save-vm=squid_trace.npy

read -p "Press enter to continue"
