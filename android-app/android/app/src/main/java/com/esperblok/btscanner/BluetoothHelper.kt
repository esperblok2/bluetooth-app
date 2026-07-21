package com.esperblok.btscanner

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

data class BTDevice(
    val name: String,
    val address: String,
    val rssi: Int = 0,
    val bluetoothDevice: BluetoothDevice,
    val isPaired: Boolean = false,
    val batteryLevel: Int? = null,
    val deviceClass: Int = 0,
    val deviceType: String = ""
)

class BluetoothHelper(private val context: Context) {

    private val tag = "BluetoothHelper"
    private val handler = Handler(Looper.getMainLooper())
    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter
    }
    private var bleScanner: BluetoothLeScanner? = null
    private var scanning = false

    private val _devices = MutableStateFlow<List<BTDevice>>(emptyList())
    val devices: StateFlow<List<BTDevice>> = _devices

    private val _scanStatus = MutableStateFlow("Klaar om te scannen")
    val scanStatus: StateFlow<String> = _scanStatus

    private val _pairedDevices = MutableStateFlow<List<BTDevice>>(emptyList())
    val pairedDevices: StateFlow<List<BTDevice>> = _pairedDevices

    private val foundDevices = mutableMapOf<String, BTDevice>()

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            val name = device.name ?: result.scanRecord?.deviceName ?: "Onbekend"
            val btDevice = BTDevice(
                name = name,
                address = device.address,
                rssi = result.rssi,
                bluetoothDevice = device,
                isPaired = isPaired(device.address),
                deviceClass = 0,
                deviceType = getDeviceType(device.address)
            )
            foundDevices[device.address] = btDevice
            _devices.value = foundDevices.values.toList().sortedByDescending { it.rssi }
        }

        override fun onScanFailed(errorCode: Int) {
            _scanStatus.value = "Scan mislukt (foutcode: $errorCode)"
            scanning = false
        }
    }

    private val pairedReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                BluetoothDevice.ACTION_BOND_STATE_CHANGED -> {
                    val device = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                    } else {
                        @Suppress("DEPRECATION")
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                    }
                    val bondState = intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE, BluetoothDevice.BOND_NONE)
                    if (bondState == BluetoothDevice.BOND_BONDED) {
                        loadPairedDevices()
                    }
                }
            }
        }
    }

    fun isEnabled(): Boolean = bluetoothAdapter?.isEnabled == true

    fun isPaired(address: String): Boolean {
        return bluetoothAdapter?.bondedDevices?.any { it.address == address } == true
    }

    @SuppressLint("MissingPermission")
    fun loadPairedDevices() {
        val paired = mutableListOf<BTDevice>()
        bluetoothAdapter?.bondedDevices?.forEach { device ->
            paired.add(
                BTDevice(
                    name = device.name ?: "Onbekend",
                    address = device.address,
                    bluetoothDevice = device,
                    isPaired = true,
                    deviceClass = 0
                )
            )
        }
        _pairedDevices.value = paired
    }

    @SuppressLint("MissingPermission")
    fun startScan() {
        if (scanning) return
        val adapter = bluetoothAdapter ?: run {
            _scanStatus.value = "Bluetooth niet beschikbaar"
            return
        }
        if (!adapter.isEnabled) {
            _scanStatus.value = "Bluetooth is uitgeschakeld"
            return
        }

        bleScanner = adapter.bluetoothLeScanner
        if (bleScanner == null) {
            _scanStatus.value = "BLE Scanner niet beschikbaar"
            return
        }

        foundDevices.clear()
        _devices.value = emptyList()
        scanning = true
        _scanStatus.value = "Scannen..."

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        bleScanner?.startScan(null, settings, scanCallback)

        handler.postDelayed({
            if (scanning) {
                stopScan()
                if (foundDevices.isEmpty()) {
                    _scanStatus.value = "Geen apparaten gevonden"
                } else {
                    _scanStatus.value = "${foundDevices.size} appara(a)ten gevonden"
                }
            }
        }, 12000)
    }

    @SuppressLint("MissingPermission")
    fun stopScan() {
        if (!scanning) return
        scanning = false
        try {
            bleScanner?.stopScan(scanCallback)
        } catch (e: Exception) {
            Log.e(tag, "Stop scan error", e)
        }
        if (foundDevices.isNotEmpty()) {
            _scanStatus.value = "${foundDevices.size} appara(a)ten gevonden"
        }
    }

    @SuppressLint("MissingPermission")
    fun connectToDevice(address: String, onConnected: (BluetoothGatt?) -> Unit) {
        val adapter = bluetoothAdapter ?: return
        val device = adapter.getRemoteDevice(address) ?: return

        device.connectGatt(context, false, object : BluetoothGattCallback() {
            override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    gatt.discoverServices()
                    onConnected(gatt)
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    gatt.close()
                    onConnected(null)
                }
            }

            override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    readBatteryLevel(gatt)
                }
            }
        })
    }

    @SuppressLint("MissingPermission")
    private fun readBatteryLevel(gatt: BluetoothGatt) {
        val batteryService = gatt.getService(UUID.fromString("0000180f-0000-1000-8000-00805f9b34fb")) ?: return
        val batteryLevelChar = batteryService.getCharacteristic(UUID.fromString("00002a19-0000-1000-8000-00805f9b34fb")) ?: return
        gatt.readCharacteristic(batteryLevelChar)
    }

    @SuppressLint("MissingPermission")
    fun registerReceiver() {
        val filter = IntentFilter().apply {
            addAction(BluetoothDevice.ACTION_BOND_STATE_CHANGED)
        }
        context.registerReceiver(pairedReceiver, filter)
        try {
            loadPairedDevices()
        } catch (e: SecurityException) {
            Log.w(tag, "BLUETOOTH_CONNECT not yet granted, skipping paired load")
        }
    }

    fun unregisterReceiver() {
        try {
            context.unregisterReceiver(pairedReceiver)
        } catch (_: Exception) {}
    }

    @SuppressLint("MissingPermission")
    fun getDeviceType(address: String): String {
        val device = bluetoothAdapter?.getRemoteDevice(address) ?: return "Onbekend"
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            when (device.type) {
                BluetoothDevice.DEVICE_TYPE_CLASSIC -> "Classic"
                BluetoothDevice.DEVICE_TYPE_DUAL -> "Dual"
                BluetoothDevice.DEVICE_TYPE_LE -> "BLE"
                else -> "Onbekend"
            }
        } else {
            "Onbekend"
        }
    }

    fun getDeviceTypeName(deviceClass: Int): String {
        return when (deviceClass and 0x1F00) {
            0x0400 -> "Audio"
            0x0200 -> "Computer"
            0x0700 -> "Phone"
            0x0600 -> "Imaging"
            0x0500 -> "Wearable"
            0x0300 -> "Network"
            else -> "Overig"
        }
    }

    fun getEmojiForDevice(name: String): String {
        val n = name.lowercase()
        return when {
            Regex("airpod|buds|headphone|headset|ear|anc").containsMatchIn(n) -> "\uD83C\uDFA7"
            Regex("speaker|boombox|sound|jbl|marshall|sonos").containsMatchIn(n) -> "\uD83D\uDD0A"
            Regex("watch|band|fit|mi band").containsMatchIn(n) -> "\u231A"
            Regex("controller|gamepad|xbox|ps[45]").containsMatchIn(n) -> "\uD83C\uDFAE"
            Regex("mouse").containsMatchIn(n) -> "\uD83D\uDDB1\uFE0F"
            Regex("keyboard").containsMatchIn(n) -> "\u2328\uFE0F"
            Regex("phone|iphone|galaxy|pixel|xiaomi|oppo|vivo|realme").containsMatchIn(n) -> "\uD83D\uDCF1"
            Regex("tv|bravia").containsMatchIn(n) -> "\uD83D\uDCFA"
            Regex("car|bmw|tesla|ford").containsMatchIn(n) -> "\uD83D\uDE97"
            Regex("macbook|laptop|dell|lenovo|hp|asus").containsMatchIn(n) -> "\uD83D\uDCBB"
            Regex("printer|canon|epson|brother").containsMatchIn(n) -> "\uD83D\uDDA8\uFE0F"
            else -> "\uD83D\uDCB1"
        }.trim()
    }
}
