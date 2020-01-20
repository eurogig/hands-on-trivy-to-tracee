#!/usr/bin/python
  
from bcc import BPF
from time import sleep

program = """
    int hello(void *ctx) {
        bpf_trace_printk("Hello DevOps Playground\\n");
        return 0;
    }
"""

b=BPF(text=program)
b.attach_kprobe(event="sys_clone",fn_name="hello")
b.trace_print()
