ajustador.features
~~~~~~~~~~~~~~~~~~

.. toctree::
   :hidden:

   features_steady_state_more
   features_spikes_more
   features_falling_curve_more
   features_rectification_more
   features_charging_curve_more

SteadyState
```````````

.. autoclass:: ajustador.features.SteadyState
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_steady_state.py

    .. codesample::

        import measurements1
        import ajustador

        rec = measurements1.waves042811[8]
        feat = ajustador.features.SteadyState(rec)
        print(feat.report())

    .. plot:: features_steady_state2.py

    .. codesample::

        import strange1               # SUPPRESS
        import ajustador              # SUPPRESS

        rec = strange1.high_baseline_post[-1]
        feat = ajustador.features.SteadyState(rec)
        print(feat.report())

    :doc:`features_steady_state_more`

Spikes
``````

.. autoclass:: ajustador.features.Spikes
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_spikes.py

    .. codesample::

        import measurements1          # SUPPRESS
        import ajustador              # SUPPRESS

        rec = measurements1.waves042811[-1]
        feat = ajustador.features.Spikes(rec)
        print(feat.report())

    .. plot:: features_spikes2.py

    .. codesample::

        import strange1               # SUPPRESS
        import ajustador              # SUPPRESS

        rec = strange1.high_baseline_post[-1]
        feat = ajustador.features.Spikes(rec)
        print(feat.report())

    :doc:`features_spikes_more`

AHP
```

.. autoclass:: ajustador.features.AHP
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_ahp.py

    .. codesample::

        import measurements1          # SUPPRESS
        import ajustador              # SUPPRESS

        rec = measurements1.waves042811[-1]
        feat = ajustador.features.AHP(rec)
        print(feat.report())

FallingCurve
````````````

.. autoclass:: ajustador.features.FallingCurve
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_falling_curve.py

    .. codesample::

        import measurements1          # SUPPRESS
        import ajustador              # SUPPRESS

        rec = measurements1.waves042811[0]
        feat = ajustador.features.FallingCurve(rec)
        print(feat.report())

    :doc:`features_falling_curve_more`

Rectification
`````````````

.. autoclass:: ajustador.features.Rectification
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_rectification.py

    .. codesample::

        import measurements1          # SUPPRESS
        import ajustador              # SUPPRESS

        rec = measurements1.waves042811[1]
        feat = ajustador.features.Rectification(rec)
        print(feat.report())

    :doc:`features_rectification_more`

ChargingCurve
`````````````

.. autoclass:: ajustador.features.ChargingCurve
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_charging_curve.py

    .. codesample::

        import measurements1          # SUPPRESS
        import ajustador              # SUPPRESS

        rec = measurements1.waves042811[-1]
        feat = ajustador.features.ChargingCurve(rec)
        print(feat.report())

    :doc:`features_charging_curve_more`
