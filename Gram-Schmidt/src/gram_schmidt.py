import numpy as np

def pansharpen_gs(ms, pan, weights=None):
    """
    Performs pansharpening using a Gram-Schmidt approach.
    
    ms: 3D numpy array of shape (bands, H, W) for multispectral data.
    pan: 2D numpy array (H, W) for the high-resolution panchromatic band.
    weights: List or array of weights to compute the synthetic pan; if None, equal weights are used.

    Note : MS and PAN should have the same shape (already upsampled)

    Plan : 
    - Compute a synthetic panchromatic image as a weighted sum of the multispectral bands.
    - Adjust the high-resolution pan to match the statistics (mean, std) of the synthetic pan.
    - Calculate the gain factor for each MS band : covariance between the MS band and the synthetic PAN / variance of the synthetic PAN
    - Apply the Gram-Schmidt transformation
    """

    print("Starting Gram-Schmidt pansharpening...")
    if weights is None:
        weights = np.ones(ms.shape[0]) / ms.shape[0] #equal weights for all the bands if not predefined weights are provided
    
    # Compute a synthetic panchromatic image as a weighted sum of the multispectral bands.
    pan_synth = np.tensordot(weights, ms, axes=(0, 0))
    print("Synthetic panchromatic image computed.")

    # Adjust the high-resolution pan to match the statistics (mean, std) of the synthetic pan.
    pan_mean, pan_std = np.mean(pan), np.std(pan) #mean and std of the panchromatic image
    pan_synth_mean, pan_synth_std = np.mean(pan_synth), np.std(pan_synth) #mean and std of the synthetic panchromatic image
    
    # Avoid division by zero
    if pan_std == 0:
        pan_std = 1e-10
    
    pan_adjusted = (pan - pan_mean) * (pan_synth_std / pan_std) + pan_synth_mean #ensures the intensity range of the pan image is consistent with the synthetic pan
    print("High-resolution panchromatic image adjusted to synthetic pan statistics.")

    # Calculate the gain factor for each MS band 
    ms_sharp = np.zeros_like(ms, dtype=np.float32) #will hold the sharpened MS image
    for i in range(ms.shape[0]): #loop over each band
        ms_band = ms[i].astype(np.float32)
        # Compute gain as the ratio of covariance between the MS band and the synthetic PAN to the variance of the synthetic PAN
        ms_band_mean = np.mean(ms_band)
        pan_synth_mean_local = np.mean(pan_synth)
        covar = np.mean((ms_band - ms_band_mean) * (pan_synth - pan_synth_mean_local)) #covariance between the MS band and the synthetic PAN
        var_synth = np.mean((pan_synth - pan_synth_mean_local)**2) #variance of the synthetic PAN

        # Avoid division by zero
        if var_synth == 0:
            var_synth = 1e-10
        gain = covar / var_synth # This determines how much of the panchromatic image should be used to enhance the MS band
        
        # Apply the Gram-Schmidt transformation
        # Enhances the MS spatial details by adding the residual between the adjusted pan and the synthetic pan
        ms_sharp[i] = ms_band + gain * (pan_adjusted - pan_synth)
        
    print("Pansharpening completed.")
    return ms_sharp #shape : (bands, H, W)