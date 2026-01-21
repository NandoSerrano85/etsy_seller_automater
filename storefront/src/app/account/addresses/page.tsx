"use client";

import { useEffect, useState } from "react";
import { customerApi } from "@/lib/api";
import { CustomerAddress } from "@/types";
import toast from "react-hot-toast";
import { Plus, MapPin, Edit2, Trash2, Check, X } from "lucide-react";

export default function AddressesPage() {
  const [addresses, setAddresses] = useState<CustomerAddress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<CustomerAddress>>({
    first_name: "",
    last_name: "",
    address1: "",
    address2: "",
    city: "",
    state: "",
    zip_code: "",
    country: "United States",
    phone: "",
    is_default_shipping: false,
    is_default_billing: false,
  });

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    setIsLoading(true);
    try {
      const data = await customerApi.getAddresses();
      setAddresses(data);
    } catch (error) {
      console.error("Failed to fetch addresses:", error);
      toast.error("Failed to load addresses");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (editingId) {
        // Update existing address
        await customerApi.updateAddress(editingId, formData);
        toast.success("Address updated successfully!");
      } else {
        // Create new address - type assertion since form validation ensures required fields
        await customerApi.addAddress(
          formData as Omit<CustomerAddress, "id" | "customer_id">,
        );
        toast.success("Address added successfully!");
      }

      // Reset form and fetch updated addresses
      resetForm();
      await fetchAddresses();
    } catch (error: any) {
      console.error("Address save error:", error);
      const message = error.response?.data?.detail || "Failed to save address";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (address: CustomerAddress) => {
    setFormData(address);
    setEditingId(address.id);
    setIsEditing(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this address?")) {
      return;
    }

    try {
      await customerApi.deleteAddress(id);
      toast.success("Address deleted successfully!");
      await fetchAddresses();
    } catch (error: any) {
      console.error("Address delete error:", error);
      const message =
        error.response?.data?.detail || "Failed to delete address";
      toast.error(message);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      // Set as default for both shipping and billing
      await customerApi.updateAddress(id, {
        is_default_shipping: true,
        is_default_billing: true,
      });
      toast.success("Default address updated!");
      await fetchAddresses();
    } catch (error: any) {
      console.error("Set default error:", error);
      const message =
        error.response?.data?.detail || "Failed to set default address";
      toast.error(message);
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: "",
      last_name: "",
      address1: "",
      address2: "",
      city: "",
      state: "",
      zip_code: "",
      country: "United States",
      phone: "",
      is_default_shipping: false,
      is_default_billing: false,
    });
    setEditingId(null);
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Saved Addresses
            </h2>
            <p className="text-gray-600 mt-1">
              Manage your shipping and billing addresses
            </p>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-primary-700"
            >
              <Plus className="w-5 h-5" />
              Add Address
            </button>
          )}
        </div>
      </div>

      {/* Add/Edit Form */}
      {isEditing && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            {editingId ? "Edit Address" : "Add New Address"}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name *
                </label>
                <input
                  type="text"
                  name="first_name"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name *
                </label>
                <input
                  type="text"
                  name="last_name"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address *
              </label>
              <input
                type="text"
                name="address1"
                required
                placeholder="Street address"
                value={formData.address1}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div className="mb-4">
              <input
                type="text"
                name="address2"
                placeholder="Apartment, suite, etc. (optional)"
                value={formData.address2}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div className="grid md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  City *
                </label>
                <input
                  type="text"
                  name="city"
                  required
                  value={formData.city}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  State *
                </label>
                <input
                  type="text"
                  name="state"
                  required
                  placeholder="CA"
                  value={formData.state}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ZIP Code *
                </label>
                <input
                  type="text"
                  name="zip_code"
                  required
                  value={formData.zip_code}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div className="mb-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="is_default"
                  checked={
                    formData.is_default_shipping || formData.is_default_billing
                  }
                  onChange={(e) => {
                    const isDefault = e.target.checked;
                    setFormData((prev) => ({
                      ...prev,
                      is_default_shipping: isDefault,
                      is_default_billing: isDefault,
                    }));
                  }}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  Set as default address
                </span>
              </label>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-primary-600 text-white py-2 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {editingId ? "Update Address" : "Add Address"}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="bg-gray-200 text-gray-700 py-2 px-6 rounded-lg font-semibold hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Addresses List */}
      <div className="grid md:grid-cols-2 gap-4">
        {isLoading && !isEditing ? (
          <div className="col-span-2 flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : addresses.length === 0 ? (
          <div className="col-span-2 text-center py-12 bg-white rounded-lg shadow-sm">
            <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">No saved addresses yet</p>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700"
              >
                <Plus className="w-5 h-5" />
                Add Your First Address
              </button>
            )}
          </div>
        ) : (
          addresses.map((address) => {
            const isDefault =
              address.is_default_shipping || address.is_default_billing;
            return (
              <div
                key={address.id}
                className="bg-white rounded-lg shadow-sm p-6 relative border-2 border-transparent hover:border-primary-200 transition-colors"
              >
                {isDefault && (
                  <div className="absolute top-4 right-4">
                    <span className="inline-flex items-center gap-1 bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-xs font-medium">
                      <Check className="w-3 h-3" />
                      Default
                    </span>
                  </div>
                )}

                <div className="mb-4">
                  <p className="font-medium text-gray-900">
                    {address.first_name} {address.last_name}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {address.address1}
                  </p>
                  {address.address2 && (
                    <p className="text-sm text-gray-600">{address.address2}</p>
                  )}
                  <p className="text-sm text-gray-600">
                    {address.city}, {address.state} {address.zip_code}
                  </p>
                  <p className="text-sm text-gray-600">{address.country}</p>
                  {address.phone && (
                    <p className="text-sm text-gray-600 mt-1">
                      {address.phone}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(address)}
                    className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                  {!isDefault && (
                    <>
                      <button
                        onClick={() => handleSetDefault(address.id)}
                        className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 font-medium"
                      >
                        <Check className="w-4 h-4" />
                        Set Default
                      </button>
                      <button
                        onClick={() => handleDelete(address.id)}
                        className="flex items-center gap-1 text-sm text-red-600 hover:text-red-700 font-medium"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
