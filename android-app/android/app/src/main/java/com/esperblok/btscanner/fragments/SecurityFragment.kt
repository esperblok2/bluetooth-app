package com.esperblok.btscanner.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R
import com.esperblok.btscanner.SecurityManager

class SecurityFragment : Fragment() {

    private lateinit var securityManager: SecurityManager

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_security, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        securityManager = (activity as MainActivity).securityManager

        val etPin = view.findViewById<EditText>(R.id.et_pin)
        val btnSetPin = view.findViewById<Button>(R.id.btn_set_pin)
        val tvWhitelist = view.findViewById<TextView>(R.id.tv_whitelist)
        val tvBlocklist = view.findViewById<TextView>(R.id.tv_blocklist)

        if (!securityManager.pin.isNullOrEmpty()) {
            etPin.setText("****")
        }

        btnSetPin.setOnClickListener {
            val newPin = etPin.text.toString().trim()
            securityManager.updatePin(newPin)
            if (newPin.isNotEmpty()) {
                Toast.makeText(context, "PIN ingesteld", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(context, "PIN verwijderd", Toast.LENGTH_SHORT).show()
            }
        }

        updateLists(tvWhitelist, tvBlocklist)
    }

    private fun updateLists(tvWhitelist: TextView, tvBlocklist: TextView) {
        val wl = securityManager.whitelist
        if (wl.isEmpty()) {
            tvWhitelist.text = "Geen apparaten in whitelist"
        } else {
            tvWhitelist.text = wl.joinToString("\n") { "  \u2705 $it" }
        }

        val bl = securityManager.blocklist
        if (bl.isEmpty()) {
            tvBlocklist.text = "Geen apparaten in blocklist"
        } else {
            tvBlocklist.text = bl.joinToString("\n") { "  \u274C $it" }
        }
    }
}
