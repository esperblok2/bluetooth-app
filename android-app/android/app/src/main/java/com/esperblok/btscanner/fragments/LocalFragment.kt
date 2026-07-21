package com.esperblok.btscanner.fragments

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.R
import java.io.File

class LocalFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_local, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val container = view.findViewById<LinearLayout>(R.id.local_container)
        container.removeAllViews()

        addSection(container, "\uD83D\uDD0C", "Bluetooth Adapter")
        val btManager = requireContext().getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        val btAdapter = btManager?.adapter
        if (btAdapter != null) {
            addInfo(container, "Naam", btAdapter.name ?: "Onbekend")
            addInfo(container, "Adres", btAdapter.address ?: "Onbekend")
            addInfo(container, "Aan", if (btAdapter.isEnabled) "Ja" else "Nee")
            addInfo(container, "Gekoppeld", "${btAdapter.bondedDevices?.size ?: 0} apparaten")
        } else {
            addInfo(container, "Status", "Niet beschikbaar")
        }

        addSection(container, "\uD83D\uDCBB", "Apparaat Info")
        addInfo(container, "Merk", Build.MANUFACTURER)
        addInfo(container, "Model", Build.MODEL)
        addInfo(container, "Apparaat", Build.DEVICE)
        addInfo(container, "Android", "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        addInfo(container, "Build", Build.DISPLAY)

        addSection(container, "\uD83D\uDCE6", "Opslag")
        val root = File("/")
        val total = root.totalSpace / (1024 * 1024 * 1024)
        val free = root.freeSpace / (1024 * 1024 * 1024)
        val used = total - free
        addInfo(container, "Totaal", "${total} GB")
        addInfo(container, "Gebruikt", "${used} GB")
        addInfo(container, "Beschikbaar", "${free} GB")

        addSection(container, "\u2699\uFE0F", "Processor")
        addInfo(container, "Board", Build.BOARD)
        addInfo(container, "Hardware", Build.HARDWARE)
        addInfo(container, "CPU", Build.SUPPORTED_ABIS.firstOrNull() ?: "Onbekend")

        addSection(container, "\uD83D\uDCE1", "Netwerk")
        try {
            val wifiManager = requireContext().applicationContext.getSystemService(Context.WIFI_SERVICE) as? android.net.wifi.WifiManager
            val ip = wifiManager?.connectionInfo?.ipAddress ?: 0
            val ipStr = "${ip and 0xFF}.${ip shr 8 and 0xFF}.${ip shr 16 and 0xFF}.${ip shr 24 and 0xFF}"
            addInfo(container, "WiFi IP", if (ip != 0) ipStr else "Niet verbonden")
            addInfo(container, "WiFi Naam", wifiManager?.connectionInfo?.ssid?.replace("\"", "") ?: "Onbekend")
        } catch (e: Exception) {
            addInfo(container, "WiFi", "Niet beschikbaar")
        }
    }

    private fun addSection(container: LinearLayout, icon: String, title: String) {
        val tv = TextView(requireContext()).apply {
            text = "$icon $title"
            setTextColor(0xFF00D4FF.toInt())
            textSize = 18f
            setPadding(0, 32, 0, 8)
        }
        container.addView(tv)
    }

    private fun addInfo(container: LinearLayout, label: String, value: String) {
        val layout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 4, 0, 4)
        }
        val tvLabel = TextView(requireContext()).apply {
            text = label
            setTextColor(0xFF7D8590.toInt())
            textSize = 12f
        }
        val tvValue = TextView(requireContext()).apply {
            text = value
            setTextColor(0xFFE6EDF3.toInt())
            textSize = 15f
        }
        layout.addView(tvLabel)
        layout.addView(tvValue)
        container.addView(layout)
    }
}
