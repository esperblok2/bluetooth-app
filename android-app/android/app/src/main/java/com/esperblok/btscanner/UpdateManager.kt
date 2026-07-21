package com.esperblok.btscanner

import android.app.DownloadManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.Cursor
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.URL

class UpdateManager(private val context: Context) {

    private val tag = "UpdateManager"
    private val handler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    private val VERSION_URL = "https://raw.githubusercontent.com/esperblok2/bluetooth-app/main/version.json"
    private val APK_URL = "https://github.com/esperblok2/bluetooth-app/raw/main/BT-Scanner-Native.apk"
    private val CHANNEL_ID = "update_channel"
    private val NOTIFICATION_ID = 1001

    private var currentVersion = "1.0"
    private var downloadId: Long = -1

    fun setCurrentVersion(version: String) {
        currentVersion = version
    }

    fun checkForUpdates(onResult: (Boolean, String, String) -> Unit) {
        scope.launch {
            try {
                val response = withContext(Dispatchers.IO) {
                    URL(VERSION_URL).readText()
                }
                val json = JSONObject(response)
                val latestVersion = json.optString("version", currentVersion)
                val changelog = json.optString("changelog", "")

                if (latestVersion != currentVersion) {
                    onResult(true, latestVersion, changelog)
                } else {
                    onResult(false, currentVersion, "")
                }
            } catch (e: Exception) {
                Log.e(tag, "Update check failed", e)
                onResult(false, "", "")
            }
        }
    }

    fun downloadAndInstall(onProgress: ((Int) -> Unit)? = null) {
        createNotificationChannel()

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentTitle("Update downloaden...")
            .setContentText("Bezig met downloaden")
            .setProgress(100, 0, true)
            .setOngoing(true)
            .build()

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(NOTIFICATION_ID, notification)

        val request = DownloadManager.Request(Uri.parse(APK_URL))
            .setTitle("BT Scanner Update")
            .setDescription("Downloaden van nieuwe versie...")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "BT-Scanner.apk")
            .setAllowedOverMetered(true)
            .setAllowedOverRoaming(true)

        val downloadManager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        downloadId = downloadManager.enqueue(request)

        val progressThread = Thread {
            var downloading = true
            while (downloading) {
                val query = DownloadManager.Query().setFilterById(downloadId)
                val cursor: Cursor? = downloadManager.query(query)
                cursor?.use {
                    if (it.moveToFirst()) {
                        val status = it.getInt(it.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
                        val bytesDownloaded = it.getLong(it.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
                        val totalBytes = it.getLong(it.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))

                        if (totalBytes > 0) {
                            val progress = ((bytesDownloaded * 100) / totalBytes).toInt()
                            handler.post { onProgress?.invoke(progress) }

                            val updatedNotification = NotificationCompat.Builder(context, CHANNEL_ID)
                                .setSmallIcon(android.R.drawable.stat_sys_download)
                                .setContentTitle("Update downloaden...")
                                .setContentText("$progress% gedownload")
                                .setProgress(100, progress, false)
                                .setOngoing(true)
                                .build()
                            notificationManager.notify(NOTIFICATION_ID, updatedNotification)
                        }

                        if (status == DownloadManager.STATUS_SUCCESSFUL || status == DownloadManager.STATUS_FAILED) {
                            downloading = false
                        }
                    }
                }
                Thread.sleep(500)
            }

            handler.post {
                notificationManager.cancel(NOTIFICATION_ID)
                openDownloadedApk()
            }
        }
        progressThread.start()
    }

    private fun openDownloadedApk() {
        val downloadManager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        val uri = downloadManager.getUriForDownloadedFile(downloadId)

        if (uri != null) {
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "application/vnd.android.package-archive")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }

            val pendingIntent = android.app.PendingIntent.getActivity(
                context, 0, intent,
                android.app.PendingIntent.FLAG_UPDATE_CURRENT or android.app.PendingIntent.FLAG_MUTABLE
            )

            val completeNotification = NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.stat_sys_download_done)
                .setContentTitle("Update gedownload!")
                .setContentText("Tik om te installeren")
                .setContentIntent(pendingIntent)
                .setAutoCancel(true)
                .build()

            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.notify(NOTIFICATION_ID + 1, completeNotification)
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "App Updates",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Meldingen voor app updates"
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun cancelUpdate() {
        if (downloadId != -1L) {
            val downloadManager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            downloadManager.remove(downloadId)
            downloadId = -1
        }
        scope.cancel()
    }
}
