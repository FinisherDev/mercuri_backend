from rest_framework import permissions

class IsApprovedRider(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not hasattr(user, 'rider_profile'):
            self.message = {
                'error': 'Rider profile required',
                'next_step': 'Complete driver profile registration',
                'redirect': '/api/users/rider-profile/create'
                }
            return False

        rider_profile = request.user.rider_profile
        if rider_profile.verification_status == 'PENDING':
            self.message = {
                'error': 'Profile pending approval',
                'message': 'Profile currently under review.',
                }
            return False

        if rider_profile.verification_status == 'PENDING':
            self.message = {
                'error': 'Profile rejected',
                'rejection_reason': rider_profile.rejection_reason,
                'next_step': 'Update your profile and resubmit.',
                'redirect': '/api/users/rider-profile/create'
                }
            return False

        return True
