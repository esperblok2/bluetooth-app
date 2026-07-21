package com.esperblok.btscanner.fragments

import android.content.Context
import android.media.AudioManager
import android.os.Bundle
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.HidHelper
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R

class ControlFragment : Fragment() {

    private lateinit var audioManager: AudioManager
    private lateinit var hidHelper: HidHelper

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_control, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        audioManager = requireContext().getSystemService(Context.AUDIO_SERVICE) as AudioManager
        hidHelper = (activity as MainActivity).hidHelper

        // Media controls
        view.findViewById<Button>(R.id.btn_prev)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_PREVIOUS)
        }
        view.findViewById<Button>(R.id.btn_play)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)
        }
        view.findViewById<Button>(R.id.btn_next)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_NEXT)
        }
        view.findViewById<Button>(R.id.btn_stop)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_STOP)
        }

        // Volume controls
        view.findViewById<Button>(R.id.btn_vol_down)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, 0)
            Toast.makeText(context, "Volume omlaag", Toast.LENGTH_SHORT).show()
        }
        view.findViewById<Button>(R.id.btn_mute)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_TOGGLE_MUTE, 0)
            Toast.makeText(context, "Mute aan/uit", Toast.LENGTH_SHORT).show()
        }
        view.findViewById<Button>(R.id.btn_vol_up)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, 0)
            Toast.makeText(context, "Volume omhoog", Toast.LENGTH_SHORT).show()
        }

        // Keyboard controls (local)
        view.findViewById<Button>(R.id.btn_key_up)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_UP) }
        view.findViewById<Button>(R.id.btn_key_down)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_DOWN) }
        view.findViewById<Button>(R.id.btn_key_left)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_LEFT) }
        view.findViewById<Button>(R.id.btn_key_right)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_RIGHT) }
        view.findViewById<Button>(R.id.btn_key_enter)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_ENTER) }
        view.findViewById<Button>(R.id.btn_key_backspace)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_DEL)
        }

        val etType = view.findViewById<EditText>(R.id.et_type)
        view.findViewById<Button>(R.id.btn_type)?.setOnClickListener {
            val text = etType.text.toString()
            if (text.isNotEmpty()) {
                Toast.makeText(context, "Typen: $text", Toast.LENGTH_SHORT).show()
                etType.text.clear()
                val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
                imm.hideSoftInputFromWindow(etType.windowToken, 0)
            }
        }

        // HID section
        val tvHidStatus = view.findViewById<TextView>(R.id.tv_hid_status)
        val etAddress = view.findViewById<EditText>(R.id.et_hid_address)
        val btnHidConnect = view.findViewById<Button>(R.id.btn_hid_connect)
        val btnHidDisconnect = view.findViewById<Button>(R.id.btn_hid_disconnect)

        btnHidConnect?.setOnClickListener {
            val address = etAddress?.text.toString().trim()
            if (address.isEmpty()) {
                Toast.makeText(context, "Voer BT adres in", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            hidHelper.connectToDevice(address) { success, msg ->
                activity?.runOnUiThread {
                    tvHidStatus?.text = msg
                    tvHidStatus?.setTextColor(if (success) 0xFF00FF88.toInt() else 0xFFFF4466.toInt())
                }
            }
        }

        btnHidDisconnect?.setOnClickListener {
            hidHelper.disconnect()
            tvHidStatus?.text = "Niet verbonden"
            tvHidStatus?.setTextColor(0xFF7D8590.toInt())
        }

        val hidKeyMap = mapOf(
            R.id.hid_key_up to 0x52.toByte(),
            R.id.hid_key_down to 0x51.toByte(),
            R.id.hid_key_left to 0x50.toByte(),
            R.id.hid_key_right to 0x4F.toByte(),
            R.id.hid_key_enter to 0x28.toByte(),
            R.id.hid_key_back to 0x2A.toByte(),
            R.id.hid_key_space to 0x2C.toByte(),
            R.id.hid_key_tab to 0x2B.toByte(),
            R.id.hid_key_esc to 0x29.toByte()
        )

        for ((btnId, keyCode) in hidKeyMap) {
            view.findViewById<Button>(btnId)?.setOnClickListener {
                if (hidHelper.isConnected()) {
                    hidHelper.sendKeyPress(keyCode)
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ hidHelper.sendKeyRelease() }, 80)
                } else {
                    Toast.makeText(context, "Niet verbonden!", Toast.LENGTH_SHORT).show()
                }
            }
        }

        val etHidType = view.findViewById<EditText>(R.id.et_hid_type)
        view.findViewById<Button>(R.id.btn_hid_type)?.setOnClickListener {
            val text = etHidType?.text.toString()
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
                etHidType?.text?.clear()
            }
        }

        // Mouse HID
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

    private fun sendKeyEvent(keyCode: Int) {
        val time = System.currentTimeMillis()
        val event = KeyEvent(time, time, KeyEvent.ACTION_DOWN, keyCode, 0)
        audioManager.dispatchMediaKeyEvent(event)
        val upEvent = KeyEvent(time, time, KeyEvent.ACTION_UP, keyCode, 0)
        audioManager.dispatchMediaKeyEvent(upEvent)
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
