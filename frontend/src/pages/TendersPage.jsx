import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  Eye, 
  Edit3, 
  Trash2, 
  CheckSquare, 
  Square, 
  Calendar, 
  Building, 
  IndianRupee, 
  AlertCircle,
  FileCheck2,
  CheckCircle,
  HelpCircle,
  ShieldCheck,
  RotateCcw
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';

const TendersPage = () => {
  const { user, isProcurementOfficer } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Data states
  const [tenders, setTenders] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);

  // Search & Filter states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [page, setPage] = useState(1);
  const limit = 8;

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Active items for modals
  const [selectedTender, setSelectedTender] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');

  // Form State
  const initialFormState = {
    tender_ref: '',
    title: '',
    description: '',
    category: 'Goods',
    estimated_value: '',
    department: 'Central Public Procurement Directorate',
    opening_date: new Date().toISOString().slice(0, 16),
    closing_date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    status: 'Published',
    mandatory_requirements: ['UDYAM', 'GST', 'PAN', 'MAKE_IN_INDIA', 'NON_BLACKLIST'],
  };

  const [formData, setFormData] = useState(initialFormState);

  // Check query params if ?create=true
  useEffect(() => {
    if (searchParams.get('create') === 'true' && isProcurementOfficer) {
      setIsCreateOpen(true);
      searchParams.delete('create');
      setSearchParams(searchParams);
    }
  }, [searchParams, isProcurementOfficer]);

  // Fetch statutory requirement templates catalog
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const res = await api.get('/tenders/requirements/templates');
        setTemplates(res.data || []);
      } catch (err) {
        console.error('Failed to load statutory requirement templates:', err);
      }
    };
    fetchTemplates();
  }, []);

  // Fetch tenders
  const fetchTenders = async () => {
    setLoading(true);
    try {
      let url = `/tenders?page=${page}&limit=${limit}`;
      if (search.trim()) url += `&search=${encodeURIComponent(search.trim())}`;
      if (statusFilter !== 'All') url += `&status=${encodeURIComponent(statusFilter)}`;
      if (categoryFilter !== 'All') url += `&category=${encodeURIComponent(categoryFilter)}`;

      const res = await api.get(url);
      setTenders(res.data.items || []);
      setTotalCount(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch tenders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenders();
  }, [page, statusFilter, categoryFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTenders();
  };

  // Requirement toggle in form
  const toggleRequirement = (key) => {
    setFormData((prev) => {
      const exists = prev.mandatory_requirements.includes(key);
      const updated = exists
        ? prev.mandatory_requirements.filter((k) => k !== key)
        : [...prev.mandatory_requirements, key];
      return { ...prev, mandatory_requirements: updated };
    });
  };

  const selectRecommendedRequirements = () => {
    const recommended = templates.filter((t) => t.is_recommended).map((t) => t.key);
    setFormData((prev) => ({
      ...prev,
      mandatory_requirements: Array.from(new Set([...prev.mandatory_requirements, ...recommended]))
    }));
  };

  const clearAllRequirements = () => {
    setFormData((prev) => ({ ...prev, mandatory_requirements: [] }));
  };

  // Open Create Modal
  const openCreateModal = () => {
    // Generate an automatic GeM Ref format
    const autoRef = `GEM/2026/B/${Math.floor(1000000 + Math.random() * 9000000)}`;
    setFormData({
      ...initialFormState,
      tender_ref: autoRef,
    });
    setFormError('');
    setIsCreateOpen(true);
  };

  // Handle Create Submit
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError('');

    try {
      const payload = {
        ...formData,
        estimated_value: parseFloat(formData.estimated_value) || 0,
        opening_date: new Date(formData.opening_date).toISOString(),
        closing_date: new Date(formData.closing_date).toISOString(),
      };

      await api.post('/tenders', payload);
      setIsCreateOpen(false);
      setPage(1);
      fetchTenders();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create tender.');
    } finally {
      setFormLoading(false);
    }
  };

  // Open Edit Modal
  const openEditModal = (tender) => {
    setSelectedTender(tender);
    setFormData({
      tender_ref: tender.tender_ref,
      title: tender.title,
      description: tender.description || '',
      category: tender.category,
      estimated_value: tender.estimated_value,
      department: tender.department,
      opening_date: new Date(tender.opening_date).toISOString().slice(0, 16),
      closing_date: new Date(tender.closing_date).toISOString().slice(0, 16),
      status: tender.status,
      mandatory_requirements: tender.mandatory_requirements || [],
    });
    setFormError('');
    setIsEditOpen(true);
  };

  // Handle Edit Submit
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError('');

    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        estimated_value: parseFloat(formData.estimated_value) || 0,
        department: formData.department,
        opening_date: new Date(formData.opening_date).toISOString(),
        closing_date: new Date(formData.closing_date).toISOString(),
        status: formData.status,
        mandatory_requirements: formData.mandatory_requirements,
      };

      await api.put(`/tenders/${selectedTender.id}`, payload);
      setIsEditOpen(false);
      fetchTenders();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to update tender.');
    } finally {
      setFormLoading(false);
    }
  };

  // Open View Details Modal
  const openViewModal = (tender) => {
    setSelectedTender(tender);
    setIsViewOpen(true);
  };

  // Open Delete Modal
  const openDeleteModal = (tender) => {
    setSelectedTender(tender);
    setIsDeleteOpen(true);
  };

  // Handle Delete Confirmation
  const handleDeleteConfirm = async () => {
    setFormLoading(true);
    try {
      await api.delete(`/tenders/${selectedTender.id}`);
      setIsDeleteOpen(false);
      fetchTenders();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete tender.');
    } finally {
      setFormLoading(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Published':
        return <Badge variant="success">Published</Badge>;
      case 'Under Evaluation':
        return <Badge variant="warning">Under Evaluation</Badge>;
      case 'Closed':
        return <Badge variant="neutral">Closed</Badge>;
      default:
        return <Badge variant="info">Draft</Badge>;
    }
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  // Group statutory templates by category
  const groupedTemplates = templates.reduce((acc, t) => {
    const cat = t.category || 'Other Statutory Requirements';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(t);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              Tender Management
            </h2>
            <span className="text-xs bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded-full border border-blue-200">
              {totalCount} Total Tenders
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Configure tender notices and define mandatory statutory requirements for automated bidder compliance screening.
          </p>
        </div>

        <div>
          {isProcurementOfficer ? (
            <Button
              variant="primary"
              icon={Plus}
              onClick={openCreateModal}
              className="bg-blue-900 hover:bg-blue-950 text-white font-bold shadow-md w-full md:w-auto"
            >
              Create New Tender
            </Button>
          ) : (
            <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-2 rounded-lg flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Login as <strong>Procurement Officer</strong> to create/edit tenders.</span>
            </div>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search ref no, title, department..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-800"
          />
        </form>

        {/* Filters */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-600 shrink-0">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="border border-slate-300 rounded-md px-2.5 py-1 text-xs bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-800"
            >
              <option value="All">All Statuses</option>
              <option value="Published">Published</option>
              <option value="Under Evaluation">Under Evaluation</option>
              <option value="Closed">Closed</option>
              <option value="Draft">Draft</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-600 shrink-0">
            <span className="font-semibold">Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="border border-slate-300 rounded-md px-2.5 py-1 text-xs bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-800"
            >
              <option value="All">All Categories</option>
              <option value="Goods">Goods</option>
              <option value="Services">Services</option>
              <option value="Works">Works</option>
            </select>
          </div>

          {(search || statusFilter !== 'All' || categoryFilter !== 'All') && (
            <button
              onClick={() => {
                setSearch('');
                setStatusFilter('All');
                setCategoryFilter('All');
                setPage(1);
              }}
              title="Reset filters"
              className="text-xs text-slate-500 hover:text-slate-800 p-1 rounded hover:bg-slate-100 flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Tenders Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Tender Ref No.</th>
                <th className="px-5 py-3">Title & Ministry / Dept</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3">Est. Value (INR)</th>
                <th className="px-5 py-3">Statutory Criteria</th>
                <th className="px-5 py-3">Closing Date</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-5 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin"></div>
                      <span>Loading tender records...</span>
                    </div>
                  </td>
                </tr>
              ) : tenders.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-5 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <FileCheck2 className="w-8 h-8 text-slate-300" />
                      <span className="font-medium text-slate-600">No matching tenders found</span>
                      <span className="text-[11px] text-slate-400">Try adjusting your search criteria or create a new tender.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                tenders.map((tender) => (
                  <tr key={tender.id} className="hover:bg-slate-50/80 transition-colors group">
                    <td className="px-5 py-4 font-mono font-bold text-blue-950">
                      {tender.tender_ref}
                    </td>
                    <td className="px-5 py-4 max-w-sm">
                      <div className="font-semibold text-slate-900 truncate" title={tender.title}>
                        {tender.title}
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <Building className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="truncate">{tender.department}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-medium text-slate-700">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 font-medium text-slate-700 border border-slate-200">
                        {tender.category}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-bold text-slate-900">
                      {formatCurrency(tender.estimated_value)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1 flex-wrap max-w-xs">
                        <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-900 font-semibold text-[10px] border border-blue-200">
                          {tender.mandatory_requirements?.length || 0} Requirements
                        </span>
                        {tender.mandatory_requirements?.slice(0, 3).map((reqKey) => (
                          <span key={reqKey} className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 text-[10px] font-mono">
                            {reqKey}
                          </span>
                        ))}
                        {tender.mandatory_requirements?.length > 3 && (
                          <span className="text-[10px] text-slate-400">
                            +{tender.mandatory_requirements.length - 3} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-4 text-slate-600">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{formatDate(tender.closing_date)}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {getStatusBadge(tender.status)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openViewModal(tender)}
                          title="View Details"
                          className="p-1.5 text-slate-500 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {isProcurementOfficer && (
                          <>
                            {(tender.status === 'Draft' || tender.status === 'Under Evaluation') ? (
                              <button
                                onClick={() => openEditModal(tender)}
                                title={`Edit Tender (${tender.status})`}
                                className="p-1.5 text-slate-500 hover:text-amber-700 hover:bg-amber-50 rounded transition-colors"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                            ) : (
                              <span
                                title={`${tender.status} tenders are legally locked and cannot be edited.`}
                                className="p-1 text-[10px] font-mono font-semibold text-slate-400 bg-slate-100 rounded px-1.5 cursor-not-allowed"
                              >
                                Locked
                              </span>
                            )}
                            {tender.status === 'Draft' && (
                              <button
                                onClick={() => openDeleteModal(tender)}
                                title="Delete Tender (Draft only)"
                                className="p-1.5 text-slate-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-5 py-3.5 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <strong className="font-semibold text-slate-900">{tenders.length}</strong> of{' '}
            <strong className="font-semibold text-slate-900">{totalCount}</strong> tenders
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="text-xs"
            >
              Previous
            </Button>
            <span className="px-2 font-medium">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="text-xs"
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      {/* CREATE TENDER MODAL */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New GeM Procurement Tender"
        subtitle="Specify tender metadata and select mandatory statutory compliance checks"
        maxWidth="max-w-4xl"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsCreateOpen(false)}
              disabled={formLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateSubmit}
              loading={formLoading}
              className="bg-blue-900 hover:bg-blue-950 font-bold"
            >
              Publish Tender
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-6">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-xs text-red-700 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{formError}</span>
            </div>
          )}

          {/* Section 1: Tender Details */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b pb-1">
              1. Basic Tender Details
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Tender Reference Number *
                </label>
                <input
                  type="text"
                  required
                  value={formData.tender_ref}
                  onChange={(e) => setFormData({ ...formData, tender_ref: e.target.value })}
                  placeholder="GEM/2026/B/892011"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Procurement Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-800"
                >
                  <option value="Goods">Goods</option>
                  <option value="Services">Services</option>
                  <option value="Works">Works</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Tender Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Procurement of High-Performance Server Infrastructure & AI Racks"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Estimated Value (INR ₹) *
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  step="1000"
                  value={formData.estimated_value}
                  onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
                  placeholder="4500000"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Procuring Ministry / Department *
                </label>
                <input
                  type="text"
                  required
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="Ministry of Electronics & IT"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Bid Opening Date & Time *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.opening_date}
                  onChange={(e) => setFormData({ ...formData, opening_date: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Bid Closing Date & Time *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.closing_date}
                  onChange={(e) => setFormData({ ...formData, closing_date: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Tender Description & Scope of Work
                </label>
                <textarea
                  rows="2"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Provide scope, technical specifications, and delivery expectations..."
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Statutory Compliance Checklist UI */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b pb-1">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  2. Mandatory Statutory Compliance Checklist
                </h4>
                <p className="text-[11px] text-slate-500">
                  Select which statutory requirements the AI engine must automatically verify against government portals for each bidder.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={selectRecommendedRequirements}
                  className="text-[11px] font-bold text-blue-800 hover:text-blue-900 bg-blue-50 px-2.5 py-1 rounded border border-blue-200"
                >
                  Select Recommended
                </button>
                <button
                  type="button"
                  onClick={clearAllRequirements}
                  className="text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-slate-100 px-2.5 py-1 rounded"
                >
                  Clear All
                </button>
              </div>
            </div>

            {/* Checklist Grid grouped by category */}
            <div className="space-y-4 pt-1">
              {Object.entries(groupedTemplates).map(([category, items]) => (
                <div key={category} className="space-y-2">
                  <h5 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider bg-slate-50 px-2.5 py-1 rounded border border-slate-200/60">
                    {category}
                  </h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {items.map((template) => {
                      const isChecked = formData.mandatory_requirements.includes(template.key);
                      return (
                        <div
                          key={template.key}
                          onClick={() => toggleRequirement(template.key)}
                          className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                            isChecked
                              ? 'border-blue-700 bg-blue-50/50 shadow-sm'
                              : 'border-slate-200 bg-white hover:border-slate-300'
                          }`}
                        >
                          <div className="flex items-start gap-2.5">
                            <div className="mt-0.5 shrink-0 text-blue-800">
                              {isChecked ? (
                                <CheckSquare className="w-4 h-4 text-blue-800 fill-blue-100" />
                              ) : (
                                <Square className="w-4 h-4 text-slate-400" />
                              )}
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="text-xs font-bold text-slate-900">
                                  {template.name}
                                </span>
                                {template.is_recommended && (
                                  <span className="text-[9px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-semibold">
                                    Recommended
                                  </span>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                                {template.description}
                              </p>
                              <span className="inline-block font-mono text-[9px] text-slate-400 mt-1 bg-slate-100 px-1 rounded">
                                ID: {template.key}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>
      </Modal>

      {/* EDIT TENDER MODAL */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title={`Edit Tender: ${formData.tender_ref}`}
        subtitle="Modify tender terms, dates, and compliance checklist"
        maxWidth="max-w-4xl"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsEditOpen(false)}
              disabled={formLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleEditSubmit}
              loading={formLoading}
              className="bg-blue-900 hover:bg-blue-950 font-bold"
            >
              Save Changes
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-6">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-xs text-red-700 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Tender Title *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-800"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white"
              >
                <option value="Goods">Goods</option>
                <option value="Services">Services</option>
                <option value="Works">Works</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Status
              </label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white"
              >
                <option value="Draft">Draft</option>
                <option value="Published">Published</option>
                <option value="Under Evaluation">Under Evaluation</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Estimated Value (INR ₹)
              </label>
              <input
                type="number"
                value={formData.estimated_value}
                onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Ministry / Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Bid Opening Date & Time
              </label>
              <input
                type="datetime-local"
                value={formData.opening_date}
                onChange={(e) => setFormData({ ...formData, opening_date: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Bid Closing Date & Time
              </label>
              <input
                type="datetime-local"
                value={formData.closing_date}
                onChange={(e) => setFormData({ ...formData, closing_date: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          {/* Statutory checklist edit */}
          <div className="space-y-2 pt-2 border-t">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Statutory Compliance Checklist Configuration
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-60 overflow-y-auto p-1">
              {templates.map((template) => {
                const isChecked = formData.mandatory_requirements.includes(template.key);
                return (
                  <div
                    key={template.key}
                    onClick={() => toggleRequirement(template.key)}
                    className={`p-2 rounded border cursor-pointer text-xs flex items-center gap-2 ${
                      isChecked ? 'bg-blue-50 border-blue-500 font-bold' : 'bg-white border-slate-200'
                    }`}
                  >
                    {isChecked ? (
                      <CheckSquare className="w-4 h-4 text-blue-800 shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-400 shrink-0" />
                    )}
                    <span className="truncate">{template.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </form>
      </Modal>

      {/* VIEW DETAILS MODAL */}
      {selectedTender && (
        <Modal
          isOpen={isViewOpen}
          onClose={() => setIsViewOpen(false)}
          title={`Tender Details: ${selectedTender.tender_ref}`}
          subtitle={selectedTender.title}
          maxWidth="max-w-3xl"
          footer={
            <Button variant="outline" onClick={() => setIsViewOpen(false)}>
              Close
            </Button>
          }
        >
          <div className="space-y-5 text-xs">
            {/* Metadata Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-400 font-semibold uppercase text-[10px] block">Category</span>
                <span className="font-bold text-slate-800 text-sm mt-0.5 block">{selectedTender.category}</span>
              </div>
              <div>
                <span className="text-slate-400 font-semibold uppercase text-[10px] block">Estimated Value</span>
                <span className="font-bold text-slate-900 text-sm mt-0.5 block">{formatCurrency(selectedTender.estimated_value)}</span>
              </div>
              <div>
                <span className="text-slate-400 font-semibold uppercase text-[10px] block">Status</span>
                <div className="mt-1">{getStatusBadge(selectedTender.status)}</div>
              </div>
              <div>
                <span className="text-slate-400 font-semibold uppercase text-[10px] block">Closing Date</span>
                <span className="font-bold text-slate-800 text-sm mt-0.5 block">{formatDate(selectedTender.closing_date)}</span>
              </div>
            </div>

            {/* Department */}
            <div>
              <span className="text-slate-500 font-bold uppercase tracking-wider text-[11px] block mb-1">
                Procuring Authority
              </span>
              <p className="text-slate-800 font-medium bg-white p-3 rounded-lg border border-slate-200">
                {selectedTender.department}
              </p>
            </div>

            {/* Scope / Description */}
            <div>
              <span className="text-slate-500 font-bold uppercase tracking-wider text-[11px] block mb-1">
                Description & Scope
              </span>
              <p className="text-slate-700 bg-white p-3 rounded-lg border border-slate-200 leading-relaxed whitespace-pre-wrap">
                {selectedTender.description || 'No detailed scope provided.'}
              </p>
            </div>

            {/* Mandatory Statutory Requirements */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                  Mandatory Statutory Compliance Criteria ({selectedTender.mandatory_requirements?.length || 0})
                </span>
                <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  AI Multi-Portal Cross-Check Configured
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {selectedTender.mandatory_requirements?.map((reqKey) => {
                  const tmpl = templates.find((t) => t.key === reqKey);
                  return (
                    <div
                      key={reqKey}
                      className="p-2.5 rounded-lg border border-slate-200 bg-white flex items-start gap-2.5 shadow-sm"
                    >
                      <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                      <div>
                        <div className="font-bold text-slate-800">
                          {tmpl ? tmpl.name : reqKey}
                        </div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {tmpl ? tmpl.description : `Statutory verification rule: ${reqKey}`}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Audit info */}
            <div className="text-[11px] text-slate-400 pt-2 border-t flex items-center justify-between">
              <span>Created by: <strong>{selectedTender.created_by_name || 'Procurement Officer'}</strong></span>
              <span>Published on: {formatDate(selectedTender.created_at)}</span>
            </div>
          </div>
        </Modal>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {selectedTender && (
        <Modal
          isOpen={isDeleteOpen}
          onClose={() => setIsDeleteOpen(false)}
          title="Delete Tender Confirmation"
          maxWidth="max-w-md"
          footer={
            <>
              <Button
                variant="ghost"
                onClick={() => setIsDeleteOpen(false)}
                disabled={formLoading}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDeleteConfirm}
                loading={formLoading}
                className="font-bold"
              >
                Confirm Delete
              </Button>
            </>
          }
        >
          <div className="space-y-3">
            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to delete tender <strong className="font-mono text-slate-900">{selectedTender.tender_ref}</strong> ({selectedTender.title})?
            </p>
            <p className="text-[11px] text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-200">
              This action removes the tender and any associated compliance configurations from the system.
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default TendersPage;
