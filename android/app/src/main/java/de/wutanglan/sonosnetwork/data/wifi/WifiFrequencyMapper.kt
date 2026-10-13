package de.wutanglan.sonosnetwork.data.wifi

import android.net.wifi.ScanResult

object WifiFrequencyMapper {

    fun frequencyToBand(frequencyMhz: Int): String {
        return if (frequencyMhz in 2400..2500) "2.4GHz" else "5GHz"
    }

    fun frequencyToChannel(frequencyMhz: Int): Int {
        return when {
            frequencyMhz == 2484 -> 14
            frequencyMhz in 2412..2472 -> (frequencyMhz - 2407) / 5
            frequencyMhz in 5000..5900 -> (frequencyMhz - 5000) / 5
            else -> 0
        }
    }

    fun centerFrequencyToChannel(centerFreq0Mhz: Int, primaryChannel: Int): Int {
        if (centerFreq0Mhz <= 0) return primaryChannel
        return when {
            centerFreq0Mhz == 2484 -> 14
            centerFreq0Mhz < 3000 -> (centerFreq0Mhz - 2407) / 5
            centerFreq0Mhz in 5000..5900 -> (centerFreq0Mhz - 5000) / 5
            else -> primaryChannel
        }
    }

    fun channelWidthMhz(channelWidthCode: Int): Int {
        return when (channelWidthCode) {
            ScanResult.CHANNEL_WIDTH_20MHZ -> 20
            ScanResult.CHANNEL_WIDTH_40MHZ -> 40
            ScanResult.CHANNEL_WIDTH_80MHZ -> 80
            ScanResult.CHANNEL_WIDTH_160MHZ -> 160
            ScanResult.CHANNEL_WIDTH_80MHZ_PLUS_MHZ -> 80
            else -> 20
        }
    }
}
