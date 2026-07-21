package com.esperblok.btscanner

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.Context
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

class HidHelper(private val context: Context) {

    private val tag = "HidHelper"
    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter
    }

    private val _connectedDevices = MutableStateFlow<List<String>>(emptyList())
    val connectedDevices: StateFlow<List<String>> = _connectedDevices

    private var inputDevice: BluetoothDevice? = null
    private var gatt: BluetoothGatt? = null
    private var controlPoint: BluetoothGattCharacteristic? = null

    companion object {
        val HID_SERVICE_UUID = UUID.fromString("00001812-0000-1000-8000-00805f9b34fb")
        val HID_REPORT_MAP_UUID = UUID.fromString("00002A4B-0000-1000-8000-00805f9b34fb")
        val HID_INFORMATION_UUID = UUID.fromString("00002A4A-0000-1000-8000-00805f9b34fb")
        val HID_REPORT_UUID = UUID.fromString("00002A4D-0000-1000-8000-00805f9b34fb")
    }

    @SuppressLint("MissingPermission")
    fun connectToDevice(address: String, onResult: (Boolean, String) -> Unit) {
        val adapter = bluetoothAdapter ?: run {
            onResult(false, "Bluetooth niet beschikbaar")
            return
        }

        val device = adapter.getRemoteDevice(address) ?: run {
            onResult(false, "Apparaat niet gevonden")
            return
        }

        device.connectGatt(context, false, object : BluetoothGattCallback() {
            override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    inputDevice = device
                    this@HidHelper.gatt = gatt
                    gatt.discoverServices()
                    onResult(true, "Verbonden met ${device.name ?: address}")
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    inputDevice = null
                    this@HidHelper.gatt = null
                    gatt.close()
                    onResult(false, "Ontkoppeld")
                }
            }

            override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    val service = gatt.getService(HID_SERVICE_UUID)
                    controlPoint = service?.getCharacteristic(HID_REPORT_UUID)
                }
            }

            override fun onCharacteristicWrite(
                gatt: BluetoothGatt,
                characteristic: BluetoothGattCharacteristic,
                status: Int
            ) {
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    Log.e(tag, "Write failed: $status")
                }
            }
        })
    }

    @SuppressLint("MissingPermission")
    fun sendKeyboardReport(keys: ByteArray) {
        val cp = controlPoint ?: return
        gatt?.writeCharacteristic(cp, keys, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
    }

    fun sendKeyPress(keyCode: Byte) {
        val report = byteArrayOf(0x00, 0x00, keyCode, 0x00, 0x00, 0x00, 0x00, 0x00)
        sendKeyboardReport(report)
    }

    fun sendKeyRelease() {
        val report = byteArrayOf(0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
        sendKeyboardReport(report)
    }

    @SuppressLint("MissingPermission")
    fun sendMouseMove(dx: Byte, dy: Byte) {
        val report = byteArrayOf(0x00, dx, dy, 0x00)
        controlPoint?.let { cp ->
            gatt?.writeCharacteristic(cp, report, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        }
    }

    @SuppressLint("MissingPermission")
    fun sendMouseClick(button: Byte) {
        val reportDown = byteArrayOf(button, 0x00, 0x00, 0x00)
        val reportUp = byteArrayOf(0x00, 0x00, 0x00, 0x00)
        controlPoint?.let { cp ->
            gatt?.writeCharacteristic(cp, reportDown, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
            Thread.sleep(50)
            gatt?.writeCharacteristic(cp, reportUp, BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)
        }
    }

    fun disconnect() {
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        inputDevice = null
        controlPoint = null
    }

    fun isConnected(): Boolean = gatt != null
}
