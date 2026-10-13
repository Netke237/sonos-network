package de.wutanglan.sonosnetwork.data.wifi

import android.net.wifi.ScanResult
import org.junit.Assert.assertEquals
import org.junit.Test

class WifiFrequencyMapperTest {

    @Test
    fun testFrequencyToChannel24GHz() {
        assertEquals(1, WifiFrequencyMapper.frequencyToChannel(2412))
        assertEquals(6, WifiFrequencyMapper.frequencyToChannel(2437))
        assertEquals(11, WifiFrequencyMapper.frequencyToChannel(2462))
        assertEquals(13, WifiFrequencyMapper.frequencyToChannel(2472))
        assertEquals(14, WifiFrequencyMapper.frequencyToChannel(2484))
    }

    @Test
    fun testFrequencyToChannel5GHz() {
        assertEquals(36, WifiFrequencyMapper.frequencyToChannel(5180))
        assertEquals(40, WifiFrequencyMapper.frequencyToChannel(5200))
        assertEquals(44, WifiFrequencyMapper.frequencyToChannel(5220))
        assertEquals(48, WifiFrequencyMapper.frequencyToChannel(5240))
        assertEquals(100, WifiFrequencyMapper.frequencyToChannel(5500))
        assertEquals(149, WifiFrequencyMapper.frequencyToChannel(5745))
    }

    @Test
    fun testBandIdentification() {
        assertEquals("2.4GHz", WifiFrequencyMapper.frequencyToBand(2412))
        assertEquals("2.4GHz", WifiFrequencyMapper.frequencyToBand(2484))
        assertEquals("5GHz", WifiFrequencyMapper.frequencyToBand(5180))
        assertEquals("5GHz", WifiFrequencyMapper.frequencyToBand(5500))
    }

    @Test
    fun testCenterFrequencyToChannelPreventsNegativeNumbersOn24GHz() {
        // 2.4 GHz 40 MHz channel bonded (e.g. Ch 1 + Ch 5 bonded -> center freq 2422 MHz)
        // Without band check, (2422 - 5000) / 5 would be -515!
        // With band check, (2422 - 2407) / 5 = 3!
        val center24G = WifiFrequencyMapper.centerFrequencyToChannel(2422, primaryChannel = 1)
        assertEquals(3, center24G)

        // 5 GHz 80 MHz channel (Ch 44 with center freq 5210 MHz -> Ch 42)
        val center5G = WifiFrequencyMapper.centerFrequencyToChannel(5210, primaryChannel = 44)
        assertEquals(42, center5G)

        // Fallback when centerFreq0 is 0
        val centerFallback = WifiFrequencyMapper.centerFrequencyToChannel(0, primaryChannel = 6)
        assertEquals(6, centerFallback)
    }

    @Test
    fun testChannelWidthMapping() {
        assertEquals(20, WifiFrequencyMapper.channelWidthMhz(ScanResult.CHANNEL_WIDTH_20MHZ))
        assertEquals(40, WifiFrequencyMapper.channelWidthMhz(ScanResult.CHANNEL_WIDTH_40MHZ))
        assertEquals(80, WifiFrequencyMapper.channelWidthMhz(ScanResult.CHANNEL_WIDTH_80MHZ))
        assertEquals(160, WifiFrequencyMapper.channelWidthMhz(ScanResult.CHANNEL_WIDTH_160MHZ))
    }
}
