package com.esperblok.btscanner.fragments

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.HidHelper
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R

class HidFragment : Fragment() {

    private lateinit var hidHelper: HidHelper
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_hid, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        hidHelper = (activity as MainActivity).hidHelper

        val tvStatus = view.findViewById<TextView>(R.id.tv_hid_status)
        val etAddress = view.findViewById<EditText>(R.id.et_hid_address)
        val btnConnect = view.findViewById<Button>(R.id.btn_hid_connect)
        val btnDisconnect = view.findViewById<Button>(R.id.btn_hid_disconnect)

        btnConnect.setOnClickListener {
            val address = etAddress.text.toString().trim()
            if (address.isEmpty()) {
                Toast.makeText(context, "Voer Bluetooth adres in", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            hidHelper.connectToDevice(address) { success, msg ->
                handler.post {
                    tvStatus.text = msg
                    tvStatus.setTextColor(if (success) 0xFF00FF88.toInt() else 0xFFFF4466.toInt())
                }
            }
        }

        btnDisconnect.setOnClickListener {
            hidHelper.disconnect()
            tvStatus.text = "Niet verbonden"
            tvStatus.setTextColor(0xFF7D8590.toInt())
        }

        val keyMap = mapOf(
            R.id.hid_key_up to 0x52.toByte(),
            R.id.hid_key_down to 0x51.toByte(),
            R.id.hid_key_left to 0x50.toByte(),
            R.id.hid_key_right to 0x4F.toByte(),
            R.id.hid_key_enter to 0x28.toByte(),
            R.id.hid_key_back to 0x2A.toByte(),
            R.id.hid_key_space to 0x2C.toByte(),
            R.id.hid_key_tab to 0x2B.toByte(),
            R.id.hid_key_esc to 0x29.toByte(),
            R.id.hid_key_a to 0x04.toByte(),
            R.id.hid_key_b to 0x05.toByte(),
            R.id.hid_key_c to 0x06.toByte()
        )

        for ((btnId, keyCode) in keyMap) {
            view.findViewById<Button>(btnId)?.setOnClickListener {
                if (hidHelper.isConnected()) {
                    hidHelper.sendKeyPress(keyCode)
                    handler.postDelayed({ hidHelper.sendKeyRelease() }, 80)
                } else {
                    Toast.makeText(context, "Niet verbonden!", Toast.LENGTH_SHORT).show()
                }
            }
        }

        val etType = view.findViewById<EditText>(R.id.et_hid_type)
        view.findViewById<Button>(R.id.btn_hid_type)?.setOnClickListener {
            val text = etType.text.toString()
            if (!hidHelper.isConnected()) {
                Toast.makeText(context, "Niet verbonden!", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (text.isNotEmpty()) {
                Thread {
                    for (c in text) {
                        val keyCode = charToHid(c)
                        if (keyCode != null) {
                            hidHelper.sendKeyPress(keyCode)
                            Thread.sleep(50)
                            hidHelper.sendKeyRelease()
                            Thread.sleep(30)
                        }
                    }
                }.start()
                etType.text.clear()
            }
        }

        view.findViewById<Button>(R.id.hid_mouse_left)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseClick(0x01)
        }
        view.findViewById<Button>(R.id.hid_mouse_right)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseClick(0x02)
        }
        view.findViewById<Button>(R.id.hid_mouse_up)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseMove(0, (-10).toByte())
        }
        view.findViewById<Button>(R.id.hid_mouse_down)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseMove(0, 10)
        }
        view.findViewById<Button>(R.id.hid_mouse_left_move)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseMove((-10).toByte(), 0)
        }
        view.findViewById<Button>(R.id.hid_mouse_right_move)?.setOnClickListener {
            if (hidHelper.isConnected()) hidHelper.sendMouseMove(10, 0)
        }
    }

    private fun charToHid(c: Char): Byte? {
        return when (c) {
            in 'a'..'z' -> (c - 'a' + 4).toByte()
            in 'A'..'Z' -> (c - 'A' + 4).toByte()
            in '1'..'9' -> (c - '1' + 30).toByte()
            '0' -> 39.toByte()
            ' ' -> 0x2C.toByte()
            '\n' -> 0x28.toByte()
            '.' -> 0x37.toByte()
            ',' -> 0x36.toByte()
            '-' -> 0x2D.toByte()
            ':' -> 0x33.toByte()
            '!' -> 0x1E.toByte()
            '?' -> 0x1F.toByte()
            '/' -> 0x38.toByte()
            '@' -> 0x1F.toByte()
            '#' -> 0x20.toByte()
            else -> null
        }
    }
}
