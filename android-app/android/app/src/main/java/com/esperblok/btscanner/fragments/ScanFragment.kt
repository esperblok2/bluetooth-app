package com.esperblok.btscanner.fragments

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.esperblok.btscanner.BTDevice
import com.esperblok.btscanner.BluetoothHelper
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R
import com.esperblok.btscanner.adapters.DeviceAdapter
import kotlinx.coroutines.launch

class ScanFragment : Fragment() {

    private lateinit var bluetoothHelper: BluetoothHelper
    private lateinit var adapter: DeviceAdapter
    private lateinit var btnScan: Button
    private lateinit var tvStatus: TextView
    private var isScanning = false

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        if (results.values.all { it }) {
            toggleScan()
        } else {
            Toast.makeText(context, "Bluetooth permissie vereist", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_scan, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bluetoothHelper = (activity as MainActivity).bluetoothHelper

        btnScan = view.findViewById(R.id.btn_scan)
        tvStatus = view.findViewById(R.id.tv_status)
        val rvDevices = view.findViewById<RecyclerView>(R.id.rv_devices)

        adapter = DeviceAdapter { device, action ->
            when (action) {
                "connect" -> connectDevice(device)
                "info" -> showDeviceInfo(device)
            }
        }

        rvDevices.layoutManager = LinearLayoutManager(context)
        rvDevices.adapter = adapter

        btnScan.setOnClickListener { checkPermissionsAndScan() }

        viewLifecycleOwner.lifecycleScope.launch {
            bluetoothHelper.devices.collect { devices ->
                adapter.submitList(devices)
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            bluetoothHelper.scanStatus.collect { status ->
                tvStatus.text = status
            }
        }
    }

    private fun checkPermissionsAndScan() {
        val perms = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(requireContext(), Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.BLUETOOTH_SCAN)
        }
        if (ContextCompat.checkSelfPermission(requireContext(), Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.BLUETOOTH_CONNECT)
        }
        if (ContextCompat.checkSelfPermission(requireContext(), Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }

        if (perms.isNotEmpty()) {
            permissionLauncher.launch(perms.toTypedArray())
        } else {
            toggleScan()
        }
    }

    private fun toggleScan() {
        if (isScanning) {
            bluetoothHelper.stopScan()
            btnScan.text = "Zoek Bluetooth Apparaten"
            isScanning = false
        } else {
            bluetoothHelper.startScan()
            btnScan.text = "Stop Scan"
            isScanning = true
        }
    }

    private fun connectDevice(device: BTDevice) {
        Toast.makeText(context, "Verbinden met ${device.name}...", Toast.LENGTH_SHORT).show()
        bluetoothHelper.connectToDevice(device.address) { gatt ->
            activity?.runOnUiThread {
                if (gatt != null) {
                    Toast.makeText(context, "${device.name} verbonden!", Toast.LENGTH_SHORT).show()
                    bluetoothHelper.loadPairedDevices()
                } else {
                    Toast.makeText(context, "Verbinding mislukt", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun showDeviceInfo(device: BTDevice) {
        val activity = activity as? MainActivity ?: return
        val dialog = android.app.AlertDialog.Builder(requireContext())
            .setTitle("${getEmoji(device.name)} ${device.name}")
            .setMessage(buildString {
                appendLine("Adres: ${device.address}")
                appendLine("Type: ${device.deviceType}")
                appendLine("Gekoppeld: ${if (device.isPaired) "Ja" else "Nee"}")
                if (device.batteryLevel != null) {
                    appendLine("Batterij: ${device.batteryLevel}%")
                }
            })
            .setPositiveButton("Sluiten", null)
            .create()
        dialog.show()
    }

    private fun getEmoji(name: String): String {
        val n = name.lowercase()
        return when {
            Regex("airpod|buds|headphone|headset|ear|anc").containsMatchIn(n) -> "\uD83C\uDFA7"
            Regex("speaker").containsMatchIn(n) -> "\uD83D\uDD0A"
            Regex("watch").containsMatchIn(n) -> "\u231A"
            Regex("controller|gamepad").containsMatchIn(n) -> "\uD83C\uDFAE"
            Regex("phone|iphone|galaxy").containsMatchIn(n) -> "\uD83D\uDCF1"
            else -> "\uD83D\uDCB1"
        }
    }

    override fun onPause() {
        super.onPause()
        if (isScanning) {
            bluetoothHelper.stopScan()
            btnScan.text = "Zoek Bluetooth Apparaten"
            isScanning = false
        }
    }
}
