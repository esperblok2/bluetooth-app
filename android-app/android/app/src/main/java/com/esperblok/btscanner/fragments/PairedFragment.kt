package com.esperblok.btscanner.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.esperblok.btscanner.BluetoothHelper
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R
import com.esperblok.btscanner.adapters.DeviceAdapter
import kotlinx.coroutines.launch

class PairedFragment : Fragment() {

    private lateinit var bluetoothHelper: BluetoothHelper
    private lateinit var adapter: DeviceAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_paired, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bluetoothHelper = (activity as MainActivity).bluetoothHelper

        val rvPaired = view.findViewById<RecyclerView>(R.id.rv_paired)
        adapter = DeviceAdapter { device, action ->
            if (action == "info") {
                android.app.AlertDialog.Builder(requireContext())
                    .setTitle("${device.name}")
                    .setMessage(buildString {
                        appendLine("Adres: ${device.address}")
                        appendLine("Type: ${device.deviceType}")
                        appendLine("Gekoppeld: Ja")
                        if (device.batteryLevel != null) appendLine("Batterij: ${device.batteryLevel}%")
                    })
                    .setPositiveButton("Sluiten", null)
                    .show()
            }
        }

        rvPaired.layoutManager = LinearLayoutManager(context)
        rvPaired.adapter = adapter

        viewLifecycleOwner.lifecycleScope.launch {
            bluetoothHelper.pairedDevices.collect { devices ->
                adapter.submitList(devices)
                view.findViewById<TextView>(R.id.tv_paired_title)?.text =
                    "Gekoppelde Apparaten (${devices.size})"
            }
        }

        bluetoothHelper.loadPairedDevices()
    }
}
