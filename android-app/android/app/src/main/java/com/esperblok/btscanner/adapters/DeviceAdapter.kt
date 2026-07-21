package com.esperblok.btscanner.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.esperblok.btscanner.BTDevice
import com.esperblok.btscanner.R

class DeviceAdapter(
    private val onAction: (BTDevice, String) -> Unit
) : ListAdapter<BTDevice, DeviceAdapter.DeviceViewHolder>(DeviceDiffCallback()) {

    class DeviceViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvIcon: TextView = view.findViewById(R.id.tv_icon)
        val tvName: TextView = view.findViewById(R.id.tv_name)
        val tvAddress: TextView = view.findViewById(R.id.tv_address)
        val tvBattery: TextView = view.findViewById(R.id.tv_battery)
        val btnAction: Button = view.findViewById(R.id.btn_action)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DeviceViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_device, parent, false)
        return DeviceViewHolder(view)
    }

    override fun onBindViewHolder(holder: DeviceViewHolder, position: Int) {
        val device = getItem(position)
        holder.tvIcon.text = getEmoji(device.name)
        holder.tvName.text = device.name
        holder.tvAddress.text = device.address

        if (device.batteryLevel != null) {
            holder.tvBattery.visibility = View.VISIBLE
            holder.tvBattery.text = "${device.batteryLevel}%"
            holder.tvBattery.setTextColor(
                when {
                    device.batteryLevel > 60 -> 0xFF00FF88.toInt()
                    device.batteryLevel > 20 -> 0xFFFFCC00.toInt()
                    else -> 0xFFFF4466.toInt()
                }
            )
        } else {
            holder.tvBattery.visibility = View.GONE
        }

        if (device.isPaired) {
            holder.btnAction.visibility = View.VISIBLE
            holder.btnAction.text = "Info"
            holder.btnAction.setOnClickListener { onAction(device, "info") }
        } else {
            holder.btnAction.visibility = View.VISIBLE
            holder.btnAction.text = "Verbind"
            holder.btnAction.setOnClickListener { onAction(device, "connect") }
        }

        holder.itemView.setOnClickListener { onAction(device, "info") }
    }

    private fun getEmoji(name: String): String {
        val n = name.lowercase()
        return when {
            Regex("airpod|buds|headphone|headset|ear|anc").containsMatchIn(n) -> "\uD83C\uDFA7"
            Regex("speaker|boombox|sound").containsMatchIn(n) -> "\uD83D\uDD0A"
            Regex("watch|band|fit").containsMatchIn(n) -> "\u231A"
            Regex("controller|gamepad").containsMatchIn(n) -> "\uD83C\uDFAE"
            Regex("mouse").containsMatchIn(n) -> "\uD83D\uDDB1\uFE0F"
            Regex("keyboard").containsMatchIn(n) -> "\u2328\uFE0F"
            Regex("phone|iphone|galaxy").containsMatchIn(n) -> "\uD83D\uDCF1"
            Regex("tv").containsMatchIn(n) -> "\uD83D\uDCFA"
            else -> "\uD83D\uDCB1"
        }
    }

    class DeviceDiffCallback : DiffUtil.ItemCallback<BTDevice>() {
        override fun areItemsTheSame(old: BTDevice, new: BTDevice) = old.address == new.address
        override fun areContentsTheSame(old: BTDevice, new: BTDevice) = old == new
    }
}
