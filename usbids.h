/*
 * This file was auto-generated by make_usbids.py. Don't edit!
 * Mon Sep 24 17:26:27 2018 +0300
 */

#ifndef USB_IDS_H
#define USB_IDS_H

typedef struct {
	unsigned short VendorID;
	unsigned short DeviceID;
	char* Vendor;
	char* Device;
} UsbDevStruct;

extern UsbDevStruct UsbList[];
extern unsigned int UsbListLength;

UsbDevStruct *UsbListFind(unsigned short vendor, unsigned short device);
int UsbListIsSorted(void);
void UsbListRunTests(void);

#endif
