package com.esperblok.btscanner.fragments

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
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

data class BatteryInfo(val name: String, val level: Int, val icon: String, val detail: String)

class BatteryFragment : Fragment() {

    private lateinit var bluetoothHelper: BluetoothHelper

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_battery, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bluetoothHelper = (activity as MainActivity).bluetoothHelper

        val rvBattery = view.findViewById<RecyclerView>(R.id.rv_battery)
        rvBattery.layoutManager = LinearLayoutManager(context)

        val batteryList = mutableListOf<BatteryInfo>()

        // Phone battery
        val batteryIntent = context?.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val level = batteryIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = batteryIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        val pct = if (level >= 0 && scale > 0) (level * 100 / scale) else -1
        val isCharging = batteryIntent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) == BatteryManager.BATTERY_STATUS_CHARGING

        if (pct >= 0) {
            batteryList.add(BatteryInfo(
                name = "Telefoon Batterij",
                level = pct,
                icon = "\uD83D\uDCF1",
                detail = if (isCharging) "Opladen..." else "Op batterij"
            ))
        }

        // BT device batteries
        viewLifecycleOwner.lifecycleScope.launch {
            bluetoothHelper.pairedDevices.collect { devices ->
                val btDevices = devices.filter { it.batteryLevel != null }.map { dev ->
                    BatteryInfo(
                        name = dev.name,
                        level = dev.batteryLevel!!,
                        icon = bluetoothHelper.getEmojiForDevice(dev.name),
                        detail = dev.address
                    )
                }
                val all = batteryList + btDevices
                rvBattery.adapter = BatteryAdapter(all)
            }
        }
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
