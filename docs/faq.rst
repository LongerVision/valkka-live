
FAQ 
===

2K and 4K cameras
-----------------

*I have benchmarked Valkka against an expensive commercial program.  The other program is capable of showing 20 live 2K cameras on the screen using a cheap laptop.  Valkka starts to choke with only six 2K cameras.  It sucks.*

That commercial program is not streaming at 2K resolution!  Instead, it requests the so-called "substream" from those cameras which is typically 720p or less.

If you want to benchmark against Valkka, you must use the substream address instead.

The substream address depends on the manufacturer.  For HIK, mainstream and substream addresses are typically (might vary, depending on the camera model):

::

    main stream : rtsp://user:password@ip_address
    sub stream  : rtsp://user:password@ip_address/Streaming/Channels/102

(The cameras *should* provide these addresses automatically at the "DESCRIBE" response of the RTSP protocol, but of course, that's too much to ask from chinese brands)
    
in Valkka Live camera config menu, you should then use *Streaming/Channels/102* at the *Tail* field

In Valkka's commercial version, the program switches automatically between main- and substream, depending on which one is needed (see also `here <https://elsampsa.github.io/valkka-examples/_build/html/pitfalls.html#bottlenecks>`_).

