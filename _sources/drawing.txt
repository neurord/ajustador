ajustador.drawing
~~~~~~~~~~~~~~~~~

.. automodule:: ajustador.drawing
    :members:
    :undoc-members:
    :member-order: bysource


Wave drawings
`````````````

.. plot::
    :include-source:

    import measurements1 as ms1
    from ajustador import drawing

    drawing.plot_together(ms1.waves091312)

.. plot::
    :include-source:

    import measurements1 as ms1
    from ajustador import drawing

    drawing.plot_waves(ms1.waves091312)

.. plot::
    :include-source:

    import measurements1 as ms1
    from ajustador import drawing

    drawing.plot_rectification(ms1.waves091312)
