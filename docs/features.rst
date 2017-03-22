ajustador.features
~~~~~~~~~~~~~~~~~~

.. toctree::
   :hidden:

   features_steady_state_more
   features_spikes_more
   features_falling_curve_more
   features_rectification_more
   features_charging_curve_more

.. autoclass:: ajustador.features.SteadyState
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_steady_state.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[8]
        feat = aju.features.SteadyState(rec)
        print(feat.report())

    .. plot:: features_steady_state2.py

    .. ipython:: python

        import strange1
        import ajustador as aju

        rec = strange1.high_baseline_post[-1]
        feat = aju.features.SteadyState(rec)
        print(feat.report())

    :doc:`features_steady_state_more`

.. autoclass:: ajustador.features.Spikes
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_spikes.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[-1]
        feat = aju.features.Spikes(rec)
        print(feat.report())

    .. plot:: features_spikes2.py

    .. ipython:: python

        import strange1
        import ajustador as aju

        rec = strange1.high_baseline_post[-1]
        feat = aju.features.Spikes(rec)
        print(feat.report())

    :doc:`features_spikes_more`

.. autoclass:: ajustador.features.AHP
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_ahp.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[-1]
        feat = aju.features.AHP(rec)
        print(feat.report())

.. autoclass:: ajustador.features.FallingCurve
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_falling_curve.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[0]
        feat = aju.features.FallingCurve(rec)
        print(feat.report())

    :doc:`features_falling_curve_more`

.. autoclass:: ajustador.features.Rectification
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_rectification.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[1]
        feat = aju.features.Rectification(rec)
        print(feat.report())

    :doc:`features_rectification_more`

.. autoclass:: ajustador.features.ChargingCurve
    :members:
    :undoc-members:
    :member-order: bysource

    .. plot:: features_charging_curve.py

    .. ipython:: python

        import measurements1 as ms1
        import ajustador as aju

        rec = ms1.waves042811[-1]
        feat = aju.features.ChargingCurve(rec)
        print(feat.report())

    :doc:`features_charging_curve_more`
