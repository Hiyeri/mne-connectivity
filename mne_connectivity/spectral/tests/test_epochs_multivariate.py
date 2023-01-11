"""Test frequency-domain multivariate connectivity methods."""
import mne
import numpy as np
import pytest
from mne.filter import filter_data
from mne_connectivity import (MultivariateSpectralConnectivity,
                              multivariate_spectral_connectivity_epochs)
from numpy.testing import assert_array_almost_equal, assert_array_less


def create_test_dataset_multivariate(sfreq, n_signals, n_epochs, n_times, tmin, tmax,
                        fstart, fend, trans_bandwidth=2., shift=None):
    """Create test dataset with no spurious correlations.

    Parameters
    ----------
    sfreq : float
        The simulated data sampling rate.
    n_signals : int
        The number of channels/signals to simulate.
    n_epochs : int
        The number of Epochs to simulate.
    n_times : int
        The number of time points at which the Epoch data is "sampled".
    tmin : int
        The start time of the Epoch data.
    tmax : int
        The end time of the Epoch data.
    fstart : int
        The frequency at which connectivity starts. The lower end of the
        spectral connectivity.
    fend : int
        The frequency at which connectivity ends. The upper end of the
        spectral connectivity.
    trans_bandwidth : int, optional
        The bandwidth of the filtering operation, by default 2.
    shift : int, optional
        Shift the correlated signal by a given number of samples, by default 
        None.

    Returns
    -------
    data : np.ndarray of shape (n_epochs, n_signals, n_times)
        The epoched dataset.
    times_data : np.ndarray of shape (n_times, )
        The times at which each sample of the ``data`` occurs at.
    """
    # Use a case known to have no spurious correlations (it would bad if
    # tests could randomly fail):
    rng = np.random.RandomState(0)

    data = rng.randn(n_signals, n_epochs * n_times)
    times_data = np.linspace(tmin, tmax, n_times)

    # simulate connectivity from fstart to fend
    data[1, :] = filter_data(data[0, :], sfreq, fstart, fend,
                             filter_length='auto', fir_design='firwin2',
                             l_trans_bandwidth=trans_bandwidth,
                             h_trans_bandwidth=trans_bandwidth)
    if shift is not None:
        data[1, :] = np.roll(data[1,:], shift=shift)

    # add some noise, so the spectrum is not exactly zero
    data[1, :] += 1e-2 * rng.randn(n_times * n_epochs)
    data = data.reshape(n_signals, n_epochs, n_times)
    data = np.transpose(data, [1, 0, 2])
    return data, times_data


class TestMultivarSpectralConnectivity:
    sfreq = 50.
    n_signals = 4
    n_epochs = 8
    n_times = 256
    trans_bandwidth = 2.
    tmin = 0.
    tmax = (n_times - 1) / sfreq
    fstart = 5.0
    fend = 15.0
    test_data, test_times = create_test_dataset_multivariate(
                sfreq, n_signals=n_signals, n_epochs=n_epochs, 
                n_times=n_times, tmin=tmin, tmax=tmax, 
                fstart=fstart, fend=fend, 
                trans_bandwidth=trans_bandwidth, shift=None
                )

    def test_invalid_method_or_mode(self):      
        class _InvalidClass:
            pass

        with pytest.raises(
            ValueError, 
            match='is not a valid connectivity method'
            ):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), method='notamethod'
                )

        with pytest.raises(
            ValueError, 
            match='The supplied connectivity method does not have the method'
            ):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), method=_InvalidClass,
                )

        with pytest.raises(
            ValueError, 
            match='mode has an invalid value'
            ):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), mode='notamode'
                )

    def test_invalid_fmin_or_fmax(self):

        with pytest.raises(
            ValueError, 
            match='There are no frequency points between'
            ):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), fmin=10,
                fmax=10 + 0.5 * (self.sfreq / float(self.n_times))
                )

        with pytest.raises(ValueError, match='fmax must be larger than fmin'):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), fmin=10, fmax=5
                )

        with pytest.raises(ValueError, match='fmax must be larger than fmin'):
            multivariate_spectral_connectivity_epochs(
                self.test_data, 
                indices=([[0,2]], [[1,3]]), fmin=(0, 11), fmax=(5, 10)
                )

        with pytest.raises(
            ValueError, 
            match='fmin and fmax must have the same length'
            ):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), fmin=(11,), 
                fmax=(12, 15)
                )

    def test_invalid_indices(self):
        # Indices cannot be None
        with pytest.raises(
            ValueError, match='indices must be specified'):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=None
            )
        
        # Add check for seeds and targets not being able to contain
        # intersecting values

        # Add check that seeds and targets for each connection must be a list of
        # ints
        

    def test_n_seed_or_target_components(self):

        # Add checks for n_components only being allowed to be None, or lists of
        # None, ints, or 'rank'

        # Add check that n_components cannot be <= 0

        # Check 1 seed, 1 target component
        _ = multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
            n_seed_components=[1], n_target_components=[1]
            )

        # Check 2 seed, 2 target components
        _ = multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
            n_seed_components=[2], n_target_components=[2]
            )

        # Check too many seed components
        with pytest.raises(ValueError, 
            match="The number of components to take"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=[3], n_target_components=[2]
                )

        # Check too many target components
        with pytest.raises(ValueError, 
            match="The number of components to take"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=[2], n_target_components=[3]
                )

        # Check wrong length of n_seed_components
        with pytest.raises(ValueError,
            match="n_seed_components must have the same length as"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=[2, 2], n_target_components=[2]
                )

        # Check wrong length of n_target_components
        with pytest.raises(ValueError,
            match="n_target_components must have the same length as"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=[2], n_target_components=[2, 2]
                )

        # Check n_seed_components is not a list or None
        with pytest.raises(ValueError,
            match="n_seed_components must be a tuple or None"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=2, n_target_components=[2]
                )
        
        # Check n_seed_components is not a tuple or None
        with pytest.raises(ValueError,
            match="n_target_components must be a tuple or None"):
            multivariate_spectral_connectivity_epochs(
                self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
                n_seed_components=[2], n_target_components=2
                )
        
        # Could add a test that when data is given with a certain rank, that
        # giving ['rank'] as an input for n_components, the correct number of
        # components are taken and stored in the returned connectivity object

    @pytest.mark.parametrize('mt_adaptive', [True, False])
    @pytest.mark.parametrize('mt_low_bias', [True, False])
    def test_adaptive(self, mt_adaptive, mt_low_bias):
        if mt_adaptive:
            mt_bandwidth = 1.
        else: 
            mt_bandwidth = None
        multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0]], [[1]]), method='mic', 
            mode='multitaper',sfreq=self.sfreq, mt_adaptive=mt_adaptive, 
            mt_low_bias=mt_low_bias, mt_bandwidth=mt_bandwidth)


    @pytest.mark.parametrize('method',
        ['mic', 'mim', 'gc', 'net_gc', 'trgc', 'net_trgc', 
        ['mic', 'mim', 'gc', 'net_gc', 'trgc', 'net_trgc']]
    )
    @pytest.mark.parametrize('mode', ['multitaper', 'fourier', 'cwt_morlet'])
    def test_methods_and_modes(self, method, mode):
        # define some frequencies for cwt
        cwt_freqs = np.arange(3, 24.5, 1)
        if method == 'mic' and mode == 'cwt_morlet':
            # so we also test using an array for num cycles
            cwt_n_cycles = 7 * np.ones(len(cwt_freqs))
        else:
            cwt_n_cycles = 7

        indices = ([[0]], [[1]])
        con = multivariate_spectral_connectivity_epochs(
            self.test_data, indices=indices, method=method, mode=mode,
            sfreq=self.sfreq, cwt_freqs=cwt_freqs,
            cwt_n_cycles=cwt_n_cycles
            )

        if not isinstance(method, list):
            freqs = con.attrs.get('freqs_used')
            n = con.n_epochs_used
            if isinstance(con, MultivariateSpectralConnectivity):
                times = con.attrs.get('times_used')
            else:
                times = con.times

            assert (n == self.n_epochs)
            assert_array_almost_equal(self.test_times, times)

            # Check topographies do/do not exist, and whether they have the
            # correct shape
            if 'method' == 'mic':
                results = con.get_data()
                topographies = con.topographies
                assert topographies is not None
                assert len(topographies) == 2
                for group_topos, group_inds in zip(topographies, indices):
                    assert len(group_topos) == len(group_inds)
                    con_i = 0
                    for con_topos, con_inds in zip(group_topos, group_inds):
                        assert (
                            con_topos.shape ==
                            (len(con_inds), *results[con_i].shape)
                        )
                        con_i += 1
            else:
                assert con.topographies is None
            
            if 'method' in ['gc', 'net_gc', 'trgc', 'net_trgc']:
                assert con.n_lags is not None
            else:
                assert con.n_lags is None

            # Everything below should be applicable for GC too

            upper_t = 0.3
            lower_t = 0.5

            # test the simulated signal
            gidx = np.searchsorted(freqs, (self.fstart, self.fend))
            bidx = np.searchsorted(
                freqs,
                (self.fstart - self.trans_bandwidth * 2, 
                self.fend + self.trans_bandwidth * 2)
                )
            
            # Check 0-lag, 2 signals
            data, _ = create_test_dataset_multivariate(
                self.sfreq, n_signals=2, n_epochs=self.n_epochs,
                n_times=self.n_times, tmin=self.tmin, tmax=self.tmax, 
                fstart=self.fstart, fend=self.fend, 
                trans_bandwidth=self.trans_bandwidth, shift=0
            )
            con = multivariate_spectral_connectivity_epochs(
                data, indices=([[0]], [[1]]), method=method, mode=mode, 
                sfreq=self.sfreq, cwt_freqs=cwt_freqs,
                cwt_n_cycles=cwt_n_cycles, n_seed_components=None, 
                n_target_components=None
                )
            assert_array_less(
                con.get_data(output='raveled')[ 0, :bidx[0]], lower_t
                )

            # Check 1-lag, 4 signals
            data, _ = create_test_dataset_multivariate(
                self.sfreq, n_signals=4, n_epochs=self.n_epochs, 
                n_times=self.n_times, tmin=self.tmin, tmax=self.tmax, 
                fstart=self.fstart, fend=self.fend, 
                trans_bandwidth=self.trans_bandwidth, shift=1
            )

            con = multivariate_spectral_connectivity_epochs(
                data, indices=([[0,2]], [[1,3]]), method=method, mode=mode, 
                sfreq=self.sfreq, cwt_freqs=cwt_freqs, 
                cwt_n_cycles=cwt_n_cycles, n_seed_components=None, 
                n_target_components=None
                )
            assert np.all(con.get_data('raveled')[0, gidx[0]:gidx[1]] > upper_t), \
                con.get_data()[0, gidx[0]:gidx[1]].min()

    # Add check that ValueError raised if gc_n_lags >= (n_freqs - 1) * 2

    # Could add a check that when net GC computed, results of [seeds -> targets]
    # == [targets -> seeds]*-1 (i.e. that results are sign flipped)

    # Add check that when using non-full rank data used with GC methods that
    # ValueError is raised for a matrix being non-positive-definite, and that
    # using SVD to make data full rank resolves this

    # Add check that when using non-full rank data with MIC and MIM and mode
    # 'cwt_morlet' that the non-real-valued nature of a matrix is raised in a
    # value error, and that using SVD to make the data full rank resolves this

    def test_parallel(self):
        """Test parallel computation."""
        n_jobs = 2
        multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0]], [[1]]), sfreq=self.sfreq, 
            n_jobs=n_jobs
            )

    def test_epochs_object(self):
        info = mne.create_info(
            ch_names=[f"ch_{n}" for n in range(self.n_signals)],
            sfreq=self.sfreq
            )
        epochs = mne.EpochsArray(self.test_data, info)
        
        con_from_data = multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0]], [[1]]), sfreq=self.sfreq
            )

        con_from_epochs = multivariate_spectral_connectivity_epochs(
            epochs, indices=([[0]], [[1]])
            )

        assert_array_almost_equal(
            con_from_epochs.get_data(), 
            con_from_data.get_data()
            )

        con_from_epochs = multivariate_spectral_connectivity_epochs(
            epochs, indices=([[0]], [[1]])
            )

        annotations = mne.Annotations(
            onset=[0, 3], duration=[1, 0.25],
            description=['Start', 'Noise'],
        )
        epochs.set_annotations((annotations))
        con_with_annot = multivariate_spectral_connectivity_epochs(
            epochs, indices=([[0]], [[1]])
            )
        assert_array_almost_equal(
            con_with_annot.get_data(), 
            con_from_data.get_data()
            )

        epochs = mne.EpochsArray(self.test_data, info)
        epochs.set_annotations((annotations))
        epochs.add_annotations_to_metadata()
        con_with_metadata = multivariate_spectral_connectivity_epochs(
            epochs, indices=([[0]], [[1]])
            )
        assert_array_almost_equal(
            con_with_metadata.get_data(), 
            con_from_data.get_data()
            )


    def test_faverage(self):
        multivariate_spectral_connectivity_epochs(
            self.test_data, indices=([[0,2]], [[1,3]]), sfreq=self.sfreq,
            fmin=(3, 8, 15), fmax=(7, 14, 20), faverage=True,
            )

        # Add checks that performing faverage in function call matches manual
        # result, and that same is seen for MIC topographies

    
    # Add checks that saving works (given indices and topographies can be
    # ragged, which needs to be handled carefully when saving); likewise, could
    # also check that re-loaded results match saved results after hacky
    # intervation for saving ragged arrays
