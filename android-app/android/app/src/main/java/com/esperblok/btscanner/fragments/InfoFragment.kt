package com.esperblok.btscanner.fragments

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.esperblok.btscanner.BluetoothHelper
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R
import kotlinx.coroutines.launch
import java.io.File

class InfoFragment : Fragment() {

    private lateinit var bluetoothHelper: BluetoothHelper

    data class BatteryInfo(val name: String, val level: Int, val icon: String, val detail: String)

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_info, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bluetoothHelper = (activity as MainActivity).bluetoothHelper

        // Battery section
        val rvBattery = view.findViewById<RecyclerView>(R.id.rv_battery)
        rvBattery.layoutManager = LinearLayoutManager(context)
        val batteryList = mutableListOf<BatteryInfo>()

        val batteryIntent = context?.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = batteryIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val pct = if (level >= 0 && scale > 0) (level * 100 / scale) else -1
        val isCharging = batteryIntent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) == BatteryManager.BATTERY_STATUS_CHARGING

        if (pct >= 0) {
            batteryList.add(BatteryInfo("Telefoon Batterij", pct, "\uD83D\uDCF1", if (isCharging) "Opladen..." else "Op batterij"))
        }

        viewLifecycleOwner.lifecycleScope.launch {
            bluetoothHelper.pairedDevices.collect { devices ->
                val btDevices = devices.filter { it.batteryLevel != null }.map { dev ->
                    BatteryInfo(dev.name, dev.batteryLevel!!, bluetoothHelper.getEmojiForDevice(dev.name), dev.address)
                }
                val all = batteryList + btDevices
                rvBattery.adapter = BatteryAdapter(all)
            }
        }

        // Local hardware section
        val localContainer = view.findViewById<LinearLayout>(R.id.local_info_container)
        localContainer.removeAllViews()

        addSection(localContainer, "\uD83D\uDD0C", "Bluetooth Adapter")
        val btManager = requireContext().getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        val btAdapter = btManager?.adapter
        if (btAdapter != null) {
            addInfo(localContainer, "Naam", btAdapter.name ?: "Onbekend")
            addInfo(localContainer, "Adres", btAdapter.address ?: "Onbekend")
            addInfo(localContainer, "Aan", if (btAdapter.isEnabled) "Ja" else "Nee")
            addInfo(localContainer, "Gekoppeld", "${btAdapter.bondedDevices?.size ?: 0} apparaten")
        } else {
            addInfo(localContainer, "Status", "Niet beschikbaar")
        }

        addSection(localContainer, "\uD83D\uDCBB", "Apparaat Info")
        addInfo(localContainer, "Merk", Build.MANUFACTURER)
        addInfo(localContainer, "Model", Build.MODEL)
        addInfo(localContainer, "Apparaat", Build.DEVICE)
        addInfo(localContainer, "Android", "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        addInfo(localContainer, "Build", Build.DISPLAY)

        addSection(localContainer, "\uD83D\uDCE6", "Opslag")
        val root = File("/")
        val total = root.totalSpace / (1024 * 1024 * 1024)
        val free = root.freeSpace / (1024 * 1024 * 1024)
        addInfo(localContainer, "Totaal", "${total} GB")
        addInfo(localContainer, "Beschikbaar", "${free} GB")
        addInfo(localContainer, "Gebruikt", "${total - free} GB")

        addSection(localContainer, "\u2699\uFE0F", "Processor")
        addInfo(localContainer, "Board", Build.BOARD)
        addInfo(localContainer, "Hardware", Build.HARDWARE)
        addInfo(localContainer, "CPU", Build.SUPPORTED_ABIS.firstOrNull() ?: "Onbekend")

        addSection(localContainer, "\uD83D\uDCE1", "Netwerk")
        try {
            val wifiManager = requireContext().applicationContext.getSystemService(Context.WIFI_SERVICE) as? android.net.wifi.WifiManager
            val ip = wifiManager?.connectionInfo?.ipAddress ?: 0
            val ipStr = "${ip and 0xFF}.${ip shr 8 and 0xFF}.${ip shr 16 and 0xFF}.${ip shr 24 and 0xFF}"
            addInfo(localContainer, "WiFi IP", if (ip != 0) ipStr else "Niet verbonden")
            addInfo(localContainer, "WiFi Naam", wifiManager?.connectionInfo?.ssid?.replace("\"", "") ?: "Onbekend")
        } catch (e: Exception) {
            addInfo(localContainer, "WiFi", "Niet beschikbaar")
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

    inner class BatteryAdapter(private val items: List<BatteryInfo>) :
        RecyclerView.Adapter<BatteryAdapter.ViewHolder>() {

        inner class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
            val tvIcon: TextView = view.findViewById(R.id.tv_bat_icon)
            val tvName: TextView = view.findViewById(R.id.tv_bat_name)
            val tvDetail: TextView = view.findViewById(R.id.tv_bat_detail)
            val pbBattery: ProgressBar = view.findViewById(R.id.pb_battery)
            val tvPercent: TextView = view.findViewById(R.id.tv_bat_percent)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.item_battery, parent, false)
            return ViewHolder(view)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val info = items[position]
            holder.tvIcon.text = info.icon
            holder.tvName.text = info.name
            holder.tvDetail.text = info.detail
            holder.pbBattery.progress = info.level
            holder.tvPercent.text = "${info.level}%"
            val color = when {
                info.level > 60 -> 0xFF00FF88.toInt()
                info.level > 20 -> 0xFFFFCC00.toInt()
                else -> 0xFFFF4466.toInt()
            }
            holder.tvPercent.setTextColor(color)
            holder.pbBattery.progressTintList = android.content.res.ColorStateList.valueOf(color)
        }

        override fun getItemCount() = items.size
    }
}
